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

import time
import tornado.ioloop

from construct import Container

from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.plmnid import PLMNID
from empower.datatypes.ssid import SSID
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import BT_L20
from empower.core.radioport import RadioPort
from empower.vbsp import HEADER
from empower.vbsp import PT_VERSION
from empower.vbsp import PT_BYE
from empower.vbsp import PT_REGISTER
from empower.vbsp import PT_UE_JOIN
from empower.vbsp import PT_UE_LEAVE
from empower.vbsp import E_TYPE_SINGLE
from empower.vbsp import E_TYPE_SCHED
from empower.vbsp import E_TYPE_TRIG
from empower.vbsp import E_SINGLE
from empower.vbsp import E_SCHED
from empower.vbsp import E_TRIG
from empower.vbsp import EP_ACT_ECAP
from empower.vbsp import EP_DIR_REQUEST
from empower.vbsp import EP_OPERATION_UNSPECIFIED
from empower.vbsp import CAPS_REQUEST
from empower.vbsp import UE_HO_REQUEST
from empower.vbsp import EP_ACT_UE_REPORT
from empower.vbsp import EP_OPERATION_ADD
from empower.vbsp import UE_REPORT_REQUEST
from empower.vbsp import EP_OPERATION_SUCCESS
from empower.vbsp import EP_ACT_HANDOVER
from empower.core.utils import hex_to_ether
from empower.core.utils import ether_to_hex
from empower.core.utils import get_xid
from empower.core.vbs import Cell
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

            self.log.info("Got message type %u (%s)", msg_type,
                          self.server.pt_types[msg_type].name)

            msg = self.server.pt_types[msg_type].parse(self.__buffer[offset:])
            addr = hex_to_ether(hdr.enbid)

            try:
                vbs = RUNTIME.vbses[addr]
            except KeyError:
                self.log.error("Unknown VBS %s, closing connection", addr)
                self.stream.close()
                return

            name = self.server.pt_types[msg_type].name
            handler_name = "_handle_%s" % name

            if hasattr(self, handler_name):
                self.log.info("%s from %s VBS %s seq %u",
                              name, self.addr[0], vbs.addr, hdr.seq)
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
        for imsi in list(RUNTIME.ues.keys()):
            RUNTIME.remove_ue(imsi)

        # reset state
        self.vbs.set_disconnected()
        self.vbs.last_seen = 0
        self.vbs.connection = None
        self.vbs.ports = {}
        self.vbs.supports = set()
        self.vbs = None

    def send_bye_message_to_self(self):
        """Send a unsollicited BYE message to senf."""

        for handler in self.server.pt_types_handlers[PT_BYE]:
            handler(self.vbs)

    def send_register_message_to_self(self):
        """Send a unsollicited REGISTER message to senf."""

        for handler in self.server.pt_types_handlers[PT_REGISTER]:
            handler(self.vbs)

    def send_message(self, msg, parser):
        """Send message and set common parameters."""

        msg.version = PT_VERSION
        msg.enbid = self.vbs.enb_id
        msg.seq = self.vbs.seq

        self.log.info("Sending %s to %s", parser.name, self.vbs)

        self.stream.write(parser.build(msg))

        return msg.modid

    def _handle_hello(self, vbs, hdr, event, hello):
        """Handle an incoming HELLO message.
        Args:
            hello, a HELLO message
        Returns:
            None
        """

        # New connection
        if not vbs.connection:

            # set pointer to pnfdev object
            self.vbs = vbs

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

    def send_caps_request(self):
        """Send a CAPS_REQUEST message.
        Args:
            vbs: an VBS object
        Returns:
            None
        Raises:
            TypeError: if vap is not an VAP object
        """

        caps_request = Container(type=E_TYPE_SINGLE,
                                 cellid=0,
                                 modid=get_xid(),
                                 length=CAPS_REQUEST.sizeof(),
                                 action=EP_ACT_ECAP,
                                 dir=EP_DIR_REQUEST,
                                 op=EP_OPERATION_UNSPECIFIED,
                                 dummy=0)

        self.send_message(caps_request, CAPS_REQUEST)

    def _handle_caps_response(self, vbs, hdr, event, caps):
        """Handle an incoming HELLO message.
        Args:
            hello, a CAPS message
        Returns:
            None
        """

        # clear cells
        vbs.cells = set()

        # add new cells
        for c in caps.cells:
            cell = Cell(vbs, c.pci, c.cap, c.DL_earfcn, c.DL_prbs,
                        c.UL_earfcn, c.UL_prbs)
            vbs.cells.add(cell)

        # transition to the online state
        vbs.set_online()

        # if UE reports are supported then activate them
        if bool(caps.flags.ue_report):
            self.send_ue_reports_request()

    def send_ue_reports_request(self):
        """Send a UE Reports message.
        Args:
            None
        Returns:
            None
        Raises:
            TypeError: if vap is not an VAP object
        """

        ue_report = Container(type=E_TYPE_TRIG,
                              cellid=0,
                              modid=get_xid(),
                              length=UE_REPORT_REQUEST.sizeof(),
                              action=EP_ACT_UE_REPORT,
                              dir=EP_DIR_REQUEST,
                              op=EP_OPERATION_ADD,
                              dummy=0)

        self.send_message(ue_report, UE_REPORT_REQUEST)

    def _handle_ue_report_response(self, vbs, hdr, event, ue_report):
        """Handle an incoming UE_REPORT message.
        Args:
            hello, a UE_REPORT message
        Returns:
            None
        """

        ues = {u.imsi: u for u in ue_report.ues}

        # check for new UEs
        for u in ues.values():

            # UE already known
            if u.imsi in RUNTIME.ues:
                continue

            plmn_id = PLMNID(u.plmn_id[1:].hex())
            tenant = RUNTIME.load_tenant_by_plmn_id(plmn_id)

            if not tenant:
                self.log.info("Unable to find PLMN id %s", plmn_id)
                continue

            if vbs.addr not in tenant.vbses:
                self.log.info("VBS %s not in PLMN id %s", vbs.addr, plmn_id)
                continue

            cell = None

            for c in vbs.cells:
                if c.pci == u.pci:
                    cell = c
                    break

            if not cell:
                self.log.info("PCI %u not found", u.pci)
                continue

            ue = UE(u.imsi, u.rnti, cell, plmn_id, tenant)
            ue.set_active()

            RUNTIME.ues[u.imsi] = ue
            tenant.ues[u.imsi] = ue

            self.server.send_ue_join_message_to_self(ue)

        # check for leaving UEs
        for imsi in list(RUNTIME.ues.keys()):
            if RUNTIME.ues[imsi].vbs != vbs:
                continue
            if imsi not in ues:
                RUNTIME.remove_ue(imsi)

    def send_ue_ho_request(self, ue, cell):
        """Send a UE_HO_REQUEST message.
        Args:
            None
        Returns:
            None
        Raises:
            None
        """

        ue_ho_request = Container(type=E_TYPE_SINGLE,
                                  cellid=ue.cell.pci,
                                  modid=get_xid(),
                                  length=UE_HO_REQUEST.sizeof(),
                                  action=EP_ACT_HANDOVER,
                                  dir=EP_DIR_REQUEST,
                                  op=EP_OPERATION_UNSPECIFIED,
                                  rnti=ue.rnti,
                                  target_enb=cell.vbs.enb_id,
                                  target_pci=cell.pci,
                                  cause=1)

        modid = self.send_message(ue_ho_request, UE_HO_REQUEST)

        self.server.pending[ue_ho_request.modid] = ue

    def _handle_ue_ho_response(self, vbs, hdr, event, ho):
        """Handle an incoming UE_HO_RESPONSE message.
        Args:
            ho, a UE_HO_RESPONSE message
        Returns:
            None
        """

        modid = None

        if hdr.modid in self.server.pending:
            # modid found
            modid = hdr.modid
        else:
            # if modid is not present then try to look up by rnti
            for i in self.server.pending:
                if self.server.pending[i].rnti == ho.rnti:
                    modid = i
                    break

        if not modid:
            self.log.error("Invalid modid %u", modid)
            return

        ue = self.server.pending[modid]

        if event.op == EP_OPERATION_SUCCESS:

            # UE was removed from source eNB
            if ue.is_ho_in_progress_removing():
                ue.set_ho_in_progress_adding()
                return

            # UE was added to target eNB
            if ue.is_ho_in_progress_adding():
                ue.set_active()
                return

        self.log.error("Error while performing handover")
        del self.server.pending[modid]
        RUNTIME.remove_ue(ue.imsi)
