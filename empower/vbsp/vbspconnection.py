#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

import uuid
import time
import tornado.ioloop

from construct import Container

from empower.datatypes.plmnid import PLMNID
from empower.datatypes.etheraddress import EtherAddress
from empower.vbsp import HEADER
from empower.vbsp import PT_VERSION
from empower.vbsp import PT_BYE
from empower.vbsp import PT_REGISTER
from empower.vbsp import EP_ACT_HELLO
from empower.vbsp import EP_ACT_CAPS
from empower.vbsp import E_TYPE_SINGLE
from empower.vbsp import E_TYPE_SCHED
from empower.vbsp import E_TYPE_TRIG
from empower.vbsp import E_SINGLE
from empower.vbsp import E_SCHED
from empower.vbsp import E_TRIG
from empower.vbsp import EP_OPERATION_UNSPECIFIED
from empower.vbsp import CAPS_REQUEST
from empower.vbsp import UE_HO_REQUEST
from empower.vbsp import EP_ACT_UE_REPORT
from empower.vbsp import EP_OPERATION_ADD
from empower.vbsp import UE_REPORT_REQUEST
from empower.vbsp import EP_OPERATION_SUCCESS
from empower.vbsp import EP_ACT_HANDOVER
from empower.vbsp import CAPS_TYPES
from empower.vbsp import EP_CAPS_CELL
from empower.core.utils import hex_to_ether
from empower.core.utils import get_xid
from empower.core.cellpool import Cell
from empower.core.ue import UE

from empower.main import RUNTIME

import empower.logger


class VBSPConnection:
    """VBSP Connection.

    Represents a connection to a ENB (EUTRAN Base Station) using
    the VBSP Protocol. One VBSPConnection object is created for every
    ENB in the network. The object implements the logic for handling
    incoming messages. The currently supported messages are:

    Attributes:
        stream: The stream object used to talk with the ENB.
        address: The connection source address, i.e. the ENB IP address.
        server: Pointer to the server object.
        vbs: Pointer to a VBS object.
    """

    def __init__(self, stream, addr, server):
        self.stream = stream
        self.stream.set_nodelay(True)
        self.addr = addr
        self.server = server
        self.vbs = None
        self.stream.set_close_callback(self._on_disconnect)
        self.__buffer = b''
        self._hb_interval_ms = 500
        self._hb_worker = tornado.ioloop.PeriodicCallback(self._heartbeat_cb,
                                                          self._hb_interval_ms)
        self._hb_worker.start()
        self._wait()
        self.log = empower.logger.get_logger()

    def to_dict(self):
        """Return dict representation of object."""

        return self.addr

    def _heartbeat_cb(self):
        """ Check if vbs connection is still active. Disconnect if no hellos
        have been received from the vbs for twice the hello period. """
        if self.vbs and not self.stream.closed():
            timeout = (self.vbs.period / 1000) * 3
            if (self.vbs.last_seen_ts + timeout) < time.time():
                self.log.info('Client inactive %s at %r', self.vbs.addr,
                              self.addr)
                self.stream.close()

    def _on_read(self, line):
        """ Appends bytes read from socket to a buffer. Once the full packet
        has been read the parser is invoked and the buffers is cleared. The
        parsed packet is then passed to the suitable method or dropped if the
        packet type in unknown. """

        self.__buffer = self.__buffer + line
        hdr = HEADER.parse(self.__buffer)

        if len(self.__buffer) < hdr.length:
            remaining = hdr.length - len(self.__buffer)
            self.stream.read_bytes(remaining, self._on_read)
            return

        try:
            self._trigger_message(hdr)
        except Exception as ex:
            self.log.exception(ex)
            self.stream.close()

        if not self.stream.closed():
            self._wait()

    def _trigger_message(self, hdr):

        if hdr.type == E_TYPE_SINGLE:
            event = E_SINGLE.parse(self.__buffer[HEADER.sizeof():])
            offset = HEADER.sizeof() + E_SINGLE.sizeof()
        elif hdr.type == E_TYPE_SCHED:
            event = E_SCHED.parse(self.__buffer[HEADER.sizeof():])
            offset = HEADER.sizeof() + E_SCHED.sizeof()
        elif hdr.type == E_TYPE_TRIG:
            event = E_TRIG.parse(self.__buffer[HEADER.sizeof():])
            offset = HEADER.sizeof() + E_TRIG.sizeof()
        else:
            self.log.error("Unknown event %u", hdr.type)
            return

        msg_type = event.action

        if msg_type not in self.server.pt_types:
            self.log.error("Unknown message type %u", msg_type)
            return

        if self.server.pt_types[msg_type]:

            msg = self.server.pt_types[msg_type].parse(self.__buffer[offset:])
            msg_name = self.server.pt_types[msg_type].name

            addr = EtherAddress(hdr.enbid[2:8])

            try:
                vbs = RUNTIME.vbses[addr]
            except KeyError:
                self.log.error("Unknown VBS %s, closing connection", addr)
                self.stream.close()
                return

            if not self.vbs:
                self.vbs = vbs

            valid = [EP_ACT_HELLO]
            if not self.vbs.is_connected() and msg_type not in valid:
                self.log.info("Got %s message from disconnected VBS %s seq %u",
                              msg_name, addr, hdr.seq)
                return

            valid = [EP_ACT_HELLO, EP_ACT_CAPS]
            if not self.vbs.is_online() and msg_type not in valid:
                self.log.info("Got %s message from offline VBS %s seq %u",
                              msg_name, addr, hdr.seq)
                return

            self.log.info("Got %s message from %s seq %u xid %u",
                          msg_name, self.vbs.addr, hdr.seq, hdr.xid)

            handler_name = "_handle_%s" % msg_name

            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                handler(vbs, hdr, event, msg)

            if msg_type in self.server.pt_types_handlers:
                for handler in self.server.pt_types_handlers[msg_type]:
                    handler(vbs, hdr, event, msg)

    def _wait(self):
        """ Wait for incoming packets on signalling channel """

        self.__buffer = b''
        self.stream.read_bytes(HEADER.sizeof(), self._on_read)

    def _on_disconnect(self):
        """ Handle VBS disconnection """

        if not self.vbs:
            return

        self.log.info("VBS disconnected: %s", self.vbs.addr)

        # remove hosted UEs
        for ue in list(RUNTIME.ues.values()):
            if self.vbs == ue.vbs:
                RUNTIME.remove_ue(ue.ue_id)

        # reset state
        self.vbs.set_disconnected()
        self.vbs.last_seen = 0
        self.vbs.connection = None
        self.vbs.ports = {}
        self.vbs.supports = set()
        self.vbs = None

    def send_bye_message_to_self(self):
        """Send a unsollicited BYE message to senf."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.vbs_down(self.vbs)

        for handler in self.server.pt_types_handlers[PT_BYE]:
            handler(self.vbs)

    def send_register_message_to_self(self):
        """Send a unsollicited REGISTER message to senf."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.vbs_up(self.vbs)

        for handler in self.server.pt_types_handlers[PT_REGISTER]:
            handler(self.vbs)

    def send_message(self, msg, msg_type, action, parser, cellid=0, 
                     xid=0, opcode=EP_OPERATION_UNSPECIFIED):
        """Send message and set common parameters."""

        msg.type = msg_type
        msg.version = PT_VERSION
        msg.enbid = b'\x00\x00' + self.vbs.addr.to_raw()
        msg.cellid = cellid
        if xid != 0:
            msg.xid = xid
        else:
            msg.xid = get_xid()
        msg.flags = Container(dir=1)
        msg.seq = self.vbs.seq
        msg.length = parser.sizeof()

        msg.action = action
        msg.opcode = opcode

        self.log.info("Sending %s to %s", parser.name, self.vbs)
        self.stream.write(parser.build(msg))

        return msg.xid

    def _handle_hello(self, vbs, hdr, event, _):
        """Handle an incoming HELLO message.
        Args:
            hello, a HELLO message
        Returns:
            None
        """

        # New connection
        if not vbs.connection:

            # set connection
            vbs.connection = self

            # change state
            vbs.set_connected()

            # send caps request
            self.send_caps_request()

        # Update WTP params
        vbs.period = event.interval
        vbs.last_seen = hdr.seq
        vbs.last_seen_ts = time.time()

    def _handle_caps_response(self, vbs, hdr, event, caps):
        """Handle an incoming HELLO message.
        Args:
            hello, a CAPS messagge
        Returns:
            None
        """

        # clear cells
        vbs.cells = {}

        # add new cells
        for raw_cap in caps.options:
            cap = CAPS_TYPES[raw_cap.type].parse(raw_cap.data)
            if raw_cap.type == EP_CAPS_CELL:
                cell = Cell(vbs, cap.pci, cap.cap, cap.dl_earfcn, cap.dl_prbs,
                            cap.ul_earfcn, cap.ul_prbs)
                vbs.cells[cap.pci] = cell

        # transition to the online state
        vbs.set_online()

        # if UE reports are supported then activate them
        if bool(caps.flags.ue_report):
            self.send_ue_reports_request()

    def _handle_ue_report_response(self, vbs, hdr, event, ue_report):
        """Handle an incoming UE_REPORT message.
        Args:
            hello, a UE_REPORT message
        Returns:
            None
        """

        incoming = []

        for ue in ue_report.ues:

            # UE already known, ignore.
            if RUNTIME.find_ue_by_rnti(ue.rnti, ue.pci, vbs):
                continue

            # otherwise check if we can add it
            plmn_id = PLMNID(ue.plmn_id[1:].hex())
            tenant = RUNTIME.load_tenant_by_plmn_id(plmn_id)

            if not tenant:
                self.log.info("Unable to find PLMN id %s", plmn_id)
                continue

            if vbs.addr not in tenant.vbses:
                self.log.info("VBS %s not in PLMN id %s", vbs.addr, plmn_id)
                continue

            if ue.pci not in vbs.cells:
                self.log.info("PCI %u not found", ue.pci)
                continue

            cell = vbs.cells[ue.pci]
            ue_id = uuid.uuid4()

            ue = UE(ue_id, ue.rnti, cell, tenant)

            RUNTIME.ues[ue.ue_id] = ue
            tenant.ues[ue.ue_id] = ue

            self.server.send_ue_join_message_to_self(ue)

            # save the new ue id
            incoming.append(ue.ue_id)

        # check for leaving UEs
        for ue_id in list(RUNTIME.ues.keys()):
            # handover in progress, ignoring
            if not RUNTIME.ues[ue_id].is_running():
                continue
            # ue has left due to an handover, ignore
            if RUNTIME.ues[ue_id].vbs != vbs:
                continue
            # ue already processed
            if ue_id in incoming:
                continue
            # ue has left
            RUNTIME.remove_ue(ue_id)

    def _handle_ue_ho_response(self, vbs, hdr, event, ho):
        """Handle an incoming UE_HO_RESPONSE message.

        If event.op is set to EP_OPERATION_SUCCESS, then the handover has been
        successfully performed and the origin_eNB, origin_pci, origin_rnti, and
        target_rnti are all set to their correct values. This message is always
        sent by the TARGET eNB.

        If event.op is set to EP_OPERATION_FAIL it means that the HO failed. In
        this case only the origin_eNB, origin_pci, and origin_rnti fields are
        filled. This message is always sent by the SOURCE eNB.

        Args:
            ho, a UE_HO_RESPONSE message
        Returns:
            None
        """
        
        origin_enbid = EtherAddress(ho.origin_enbid[2:8])

        if origin_enbid not in RUNTIME.vbses:
            self.log.warning("HO response from unknown VBS %s", RUNTIME.vbses)
            return

        origin_vbs = RUNTIME.vbses[origin_enbid]

        ue = RUNTIME.find_ue_by_rnti(ho.origin_rnti, ho.origin_pci, origin_vbs)

        if not ue:
            self.log.warning("Unable to find UE rnti %u pci %u vbs %s",
                             ho.origin_rnti, ho.origin_pci, origin_vbs)
            return

        ue.handle_ue_handover_response(origin_vbs, self.vbs, ho.origin_rnti, ho.target_rnti, 
                                       ho.origin_pci, hdr.cellid, event.opcode)

    def send_caps_request(self):
        """Send a CAPS_REQUEST message.
        Args:
            vbs: an VBS object
        Returns:
            None
        Raises:
            TypeError: if vap is not an VAP object
        """

        msg = Container(dummy=0)
        
        self.send_message(msg, 
                          E_TYPE_SINGLE, 
                          EP_ACT_CAPS, 
                          CAPS_REQUEST)
    
    def send_ue_reports_request(self):
        """Send a UE Reports message.
        Args:
            None
        Returns:
            None
        Raises:
            TypeError: if vap is not an VAP object
        """

        msg = Container(dummy=0)

        self.send_message(msg, 
                          E_TYPE_TRIG, 
                          EP_ACT_UE_REPORT, 
                          UE_REPORT_REQUEST, 
                          opcode=EP_OPERATION_ADD)

    def send_ue_ho_request(self, ue, cell):
        """Send a UE_HO_REQUEST message.
        Args:
            None
        Returns:
            None
        Raises:
            None
        """

        msg = Container(rnti=ue.rnti,
                        target_enbid=b'\x00\x00' + cell.vbs.addr.to_raw(),
                        target_pci=cell.pci,
                        cause=1)

        return self.send_message(msg, E_TYPE_SINGLE, EP_ACT_HANDOVER, UE_HO_REQUEST, cellid=ue.cell.pci)
