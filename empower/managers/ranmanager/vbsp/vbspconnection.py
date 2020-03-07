#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

"""VBSP Connection."""

import time

from construct import Container
from tornado.iostream import StreamClosedError

from empower.managers.ranmanager.vbsp.cellpool import Cell
from empower.managers.ranmanager.ranconnection import RANConnection
from empower.core.etheraddress import EtherAddress
from empower.managers.ranmanager.vbsp import HELLO_SERVICE_PERIOD, \
    PT_HELLO_SERVICE_PERIOD


class VBSPConnection(RANConnection):
    """A persistent connection to a VBS."""

    def on_read(self, future):
        """Assemble message from agent.

        Appends bytes read from socket to a buffer. Once the full packet
        has been read the parser is invoked and the buffers is cleared. The
        parsed packet is then passed to the suitable method or dropped if the
        packet type in unknown.
        """

        try:
            self.buffer = self.buffer + future.result()
        except StreamClosedError as stream_ex:
            self.log.error(stream_ex)
            return

        hdr = self.proto.HEADER.parse(self.buffer)

        if len(self.buffer) < hdr.length:
            remaining = hdr.length - len(self.buffer)
            future = self.stream.read_bytes(remaining)
            future.add_done_callback(self.on_read)
            return

        # Check if we know the message type
        if hdr.tsrc.action not in self.proto.PT_TYPES:
            self.log.warning("Unknown message type %u, ignoring.",
                             hdr.tsrc.action)
            return

        # Check if the Device is among the ones we known
        addr = EtherAddress(hdr.device)

        if addr not in self.manager.devices:
            self.log.warning("Unknown Device %s, closing connection.", addr)
            self.stream.close()
            return

        device = self.manager.devices[addr]

        # Log message informations
        parser = self.proto.PT_TYPES[hdr.tsrc.action][0]
        name = self.proto.PT_TYPES[hdr.tsrc.action][1]
        msg = parser.parse(self.buffer)
        self.log.debug("Got %s message from %s seq %u", name,
                       EtherAddress(addr), msg.seq)

        # If Device is not online and is not connected, then the only message
        # type we can accept is HELLO_RESPONSE
        if not device.is_connected():

            if msg.tsrc.action != self.proto.PT_HELLO_SERVICE:
                if not self.stream.closed():
                    self.wait()
                return

            # This is a new connection, set pointer to the device
            self.device = device

            # The set pointer from device connection to this object
            device.connection = self

            # Transition to connected state
            device.set_connected()

            # Start hb worker
            self.hb_worker.start()

            # Send caps request
            self.send_caps_request()

        # If device is not online but it is connected, then we can accept both
        # HELLO_RESPONSE and CAP_RESPONSE message
        if device.is_connected() and not device.is_online():
            valid = (self.proto.PT_HELLO_SERVICE,
                     self.proto.PT_CAPABILITIES_SERVICE)
            if msg.tsrc.action not in valid:
                if not self.stream.closed():
                    self.wait()
                return

        # Otherwise handle message
        try:
            self.handle_message(name, msg)
        except Exception as ex:
            self.log.exception(ex)
            self.stream.close()

        if not self.stream.closed():
            self.wait()

    def handle_message(self, method, msg):
        """Handle incoming message."""

        # If the default handler is defined then call it
        handler_name = "_handle_%s" % method
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            handler(msg)

        # Call registered callbacks
        if msg.tsrc.action in self.proto.PT_TYPES_HANDLERS:
            for handler in self.proto.PT_TYPES_HANDLERS[msg.tsrc.action]:
                handler(msg, self.device)

        # Check if there are pending XIDs
        if msg.xid in self.xids:
            request = self.xids[msg.xid][0]
            callback = self.xids[msg.xid][1]
            if callback:
                callback(msg, self.device, request)
            del self.xids[msg.xid]

    def on_disconnect(self):
        """Handle device disconnection."""

        if not self.device:
            return

        self.log.warning("Device disconnected: %s", self.device.addr)

        # Remove hosted UEQs
        ueqs = [ueq for ueq in self.manager.ueqs.values()
                if ueq.vbs.addr == self.device.addr]

        for ueq in list(ueqs):
            del self.manager.ueqs[ueq.addr]

        # reset state
        self.device.set_disconnected()
        self.device.last_seen = 0
        self.device.connection = None
        self.device.blocks = {}
        self.device = None

        # Stop hb worker
        self.hb_worker.stop()

    def send_message(self, action, msg_type, crud_result, tlvs=None,
                     callback=None):
        """Send message and set common parameters."""

        parser = self.proto.PT_TYPES[action][0]
        name = self.proto.PT_TYPES[action][1]

        if self.stream.closed():
            self.log.warning("Stream closed, unabled to send %s message to %s",
                             parser.name, self.device)
            return 0

        msg = Container()

        msg.version = self.proto.PT_VERSION
        msg.flags = Container(msg_type=msg_type)
        msg.tsrc = Container(
            crud_result=crud_result,
            action=action
        )
        msg.length = self.proto.HEADER.sizeof()
        msg.padding = 0
        msg.device = self.device.addr.to_raw()
        msg.seq = self.seq
        msg.xid = self.xid
        msg.tlvs = []

        if not tlvs:
            tlvs = []

        for tlv in tlvs:
            msg.tlvs.append(tlv)
            msg.length += tlv.length

        addr = self.stream.socket.getpeername()

        self.log.debug("Sending %s message to %s seq %u",
                       name, addr[0], msg.seq)

        self.stream.write(parser.build(msg))

        if callback:
            self.xids[msg.xid] = (msg, callback)

        return msg.xid

    def send_caps_request(self):
        """Send a CAPS_REQUEST message."""

        return self.send_message(action=self.proto.PT_CAPABILITIES_SERVICE,
                                 msg_type=self.proto.MSG_TYPE_REQUEST,
                                 crud_result=self.proto.OP_GET)

    def send_ue_reports_request(self):
        """Send a UE_REPORTS message."""

        return self.send_message(action=self.proto.PT_UE_REPORTS_SERVICE,
                                 msg_type=self.proto.MSG_TYPE_REQUEST,
                                 crud_result=self.proto.OP_GET)

    def send_hello_response(self, period):
        """Send an HELLO response message."""

        hello_tlv = Container()
        hello_tlv.period = period

        value = HELLO_SERVICE_PERIOD.build(hello_tlv)

        tlv = Container()
        tlv.type = PT_HELLO_SERVICE_PERIOD
        tlv.length = 4 + len(value)
        tlv.value = value

        return self.send_message(action=self.proto.PT_HELLO_SERVICE,
                                 msg_type=self.proto.MSG_TYPE_RESPONSE,
                                 crud_result=self.proto.RESULT_SUCCESS,
                                 tlvs=[tlv])

    def _handle_hello_service(self, msg):
        """Handle an incoming HELLO message."""

        # parse TLVs
        for tlv in msg.tlvs:

            if tlv.type not in self.proto.TLVS:
                self.log.warning("Unknown options %u", tlv.type)
                continue

            parser = self.proto.TLVS[tlv.type]
            option = parser.parse(tlv.value)

            self.log.debug("Processing options %s", parser.name)

            if tlv.type == self.proto.PT_HELLO_SERVICE_PERIOD:
                self.send_hello_response(option.period)

        self.device.last_seen = msg.seq
        self.device.last_seen_ts = time.time()

    def _handle_capabilities_service(self, msg):
        """Handle an incoming CAPABILITIES_SERVICE message."""

        # parse TLVs
        for tlv in msg.tlvs:

            if tlv.type not in self.proto.TLVS:
                self.log.warning("Unknown options %u", tlv.type)
                continue

            parser = self.proto.TLVS[tlv.type]
            option = parser.parse(tlv.value)

            self.log.debug("Processing options %s", parser.name)

            if tlv.type == self.proto.PT_CAPABILITIES_SERVICE_CELL:
                self.device.cells[option.pci] = \
                    Cell(vbs=self.device,
                         pci=option.pci,
                         dl_earfcn=option.dl_earfcn,
                         ul_earfcn=option.ul_earfcn,
                         n_prbs=option.n_prbs)

        # set state to online
        self.device.set_online()

        # enable UE reports
        self.send_ue_reports_request()
