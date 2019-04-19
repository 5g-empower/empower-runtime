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
from tornado.iostream import StreamClosedError

from construct import Container

from empower.datatypes.plmnid import PLMNID
from empower.datatypes.dscp import DSCP
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
from empower.vbsp import ENB_CAPS_REQUEST
from empower.vbsp import UE_HO_REQUEST
from empower.vbsp import EP_ACT_UE_REPORT
from empower.vbsp import UE_REPORT_REQUEST
from empower.vbsp import UE_REPORT_TYPES
from empower.vbsp import EP_UE_REPORT_IDENTITY
from empower.vbsp import EP_OPERATION_ADD
from empower.vbsp import EP_ACT_HANDOVER
from empower.vbsp import ENB_CAPS_TYPES
from empower.vbsp import EP_CELL_CAPS
from empower.vbsp import EP_RAN_CAPS
from empower.vbsp import RAN_MAC_SLICE_REQUEST
from empower.vbsp import EP_ACT_RAN_MAC_SLICE
from empower.vbsp import RAN_MAC_SLICE_RBGS
from empower.vbsp import RAN_MAC_SLICE_SCHED_ID
from empower.vbsp import RAN_MAC_SLICE_RNTI_LIST
from empower.vbsp import EP_RAN_MAC_SLICE_RBGS
from empower.vbsp import EP_RAN_MAC_SLICE_SCHED_ID
from empower.vbsp import EP_RAN_MAC_SLICE_RNTI_LIST
from empower.vbsp import RAN_MAC_SLICE_TYPES
from empower.vbsp import EP_OPERATION_REM
from empower.vbsp import EP_OPERATION_SET
from empower.vbsp import REM_RAN_MAC_SLICE_REQUEST
from empower.vbsp import SET_RAN_MAC_SLICE_REQUEST
from empower.core.cellpool import Cell
from empower.core.ue import UE
from empower.core.utils import get_xid

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

    def _on_read(self, future):
        """ Appends bytes read from socket to a buffer. Once the full packet
        has been read the parser is invoked and the buffers is cleared. The
        parsed packet is then passed to the suitable method or dropped if the
        packet type in unknown. """

        try:
            line = future.result()
            self.__buffer = self.__buffer + line
        except StreamClosedError as stream_ex:
            self.log.error(stream_ex)
            return

        hdr = HEADER.parse(self.__buffer)

        if len(self.__buffer) < hdr.length:
            remaining = hdr.length - len(self.__buffer)
            future = self.stream.read_bytes(remaining)
            future.add_done_callback(self._on_read)
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
        future = self.stream.read_bytes(HEADER.sizeof())
        future.add_done_callback(self._on_read)

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
                     opcode=EP_OPERATION_UNSPECIFIED, xid=get_xid()):
        """Send message and set common parameters."""

        msg.type = msg_type
        msg.version = PT_VERSION
        msg.enbid = b'\x00\x00' + self.vbs.addr.to_raw()
        msg.cellid = cellid
        msg.xid = xid
        msg.flags = Container(dir=1)
        msg.seq = self.vbs.seq

        msg.action = action
        msg.opcode = opcode

        self.log.info("Sending %s to %s", parser.name, self.vbs)
        self.stream.write(parser.build(msg))

        return msg.xid

    def _handle_hello(self, vbs, hdr, event, message):
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
        """Handle an incoming ENB CAPS RESPONSE message.
        Args:
            caps, a ENB CAPS messagge
        Returns:
            None
        """

        # clear cells
        vbs.cells = {}

        # parse capabilities TLVs
        for raw_cap in caps.options:

            if raw_cap.type not in ENB_CAPS_TYPES:
                self.log.warning("Unknown options %u", raw_cap)
                continue

            prop = ENB_CAPS_TYPES[raw_cap.type].name
            option = ENB_CAPS_TYPES[raw_cap.type].parse(raw_cap.data)

            self.log.warning("Processing options %s", prop)

            # handle new cells
            if raw_cap.type == EP_CELL_CAPS:

                if option.pci not in vbs.cells:

                    cell = Cell(vbs, option.pci)
                    vbs.cells[option.pci] = cell

                cell = vbs.cells[option.pci]

                cell.features = option.features
                cell.dl_earfcn = option.dl_earfcn
                cell.dl_bandwidth = option.dl_bandwidth
                cell.ul_earfcn = option.ul_earfcn
                cell.ul_bandwidth = option.ul_bandwidth
                cell.max_ues = option.max_ues

                if option.features.ue_report:
                    # activate UE reports
                    self.send_ue_reports_request()

            # handle ran capabilities
            if raw_cap.type == EP_RAN_CAPS:

                ran_features = {}

                ran_features['layer1'] = option.layer1
                ran_features['layer2'] = {}

                ran_features['layer2']['rbg_slicing'] = option.layer2.rbg_slicing
                ran_features['layer2']['prb_slicing'] = option.layer2.prb_slicing

                ran_features['layer3'] = option.layer3
                ran_features['mac_sched'] = option.mac_sched
                ran_features['max_slices'] = option.max_slices

                if option.pci not in vbs.cells:

                    cell = Cell(vbs, option.pci)
                    vbs.cells[option.pci] = cell

                cell = vbs.cells[option.pci]

                cell.ran_features = ran_features

                # send slice request
                self.send_ran_mac_slice_request(option.pci)

                # send slices
                self.update_slices()

        # transition to the online state
        vbs.set_online()

    def update_slices(self):
        """Update active Slices."""

        for tenant in RUNTIME.tenants.values():

            # vbs not in this tenant
            if self.vbs.addr not in tenant.vbses:
                continue

            # send slices configuration
            for slc in tenant.slices.values():

                if not tenant.plmn_id:
                    continue

                if not slc.lte['vbses'] or \
                    (slc.lte['vbses'] and self.vbs.addr in slc.lte['vbses']):

                    for cell in self.vbs.cells.values():

                        if self.vbs.addr not in slc.lte['vbses']:

                            self.vbs.connection. \
                                send_add_set_ran_mac_slice_request(cell,
                                                                   slc,
                                                                   EP_OPERATION_ADD)
                        else:
                            self.vbs.connection.\
                                send_add_set_ran_mac_slice_request(cell,
                                                                   slc,
                                                                   EP_OPERATION_SET)

    def _handle_ue_report_response(self, vbs, hdr, event, msg):
        """Handle an incoming UE_REPORT message.
        Args:
            hello, a UE_REPORT message
        Returns:
            None
        """

        for raw_entry in msg.options:

            if raw_entry.type not in UE_REPORT_TYPES:
                self.log.warning("Unknown options %u", raw_entry)
                continue

            prop = UE_REPORT_TYPES[raw_entry.type].name
            option = UE_REPORT_TYPES[raw_entry.type].parse(raw_entry.data)

            self.log.warning("Processing options %s", prop)

            if raw_entry.type == EP_UE_REPORT_IDENTITY:

                # NOTE: These ID generation should fallback to a data-type like for PLMNID
                imsi_id = uuid.UUID(int=option.imsi)
                tmsi_id = uuid.UUID(int=option.tmsi)

                # VBS can have multiple carriers (cells), and each carrier can allocate
                # its own RNTI range independently. This means that on UUID generation
                # by RNTI you can get multiple different UEs with the same UUID if only
                # RNTI is considered. This gives to the ID a little of context.
                rnti_id = uuid.UUID(int=vbs.addr.to_int() << 32 | hdr.cellid << 16 | option.rnti)

                plmn_id = PLMNID(option.plmn_id)
                tenant = RUNTIME.load_tenant_by_plmn_id(plmn_id)

                if not tenant:
                    self.log.info("Unknown tenant %s", plmn_id)
                    continue

                # Basic fallback mechanism for UE unique ID generation
                #
                # IMSI
                #   UE ID is generated using the Subscriber Identity, thus it
                #   will remain stable through multiple connection/disconnection
                if option.imsi != 0:
                    ue_id = imsi_id

                # TMSI
                #   UE ID is generated using Temporary ID assigned by the Core
                #   Network, and will be stable depending on the CN ID generation
                #   behavior
                elif option.tmsi != 0:
                    ue_id = tmsi_id

                # RNTI
                #   UE ID is generated using the Radio Network Temporary
                #   Identifier. This means that at any event where such identifier
                #   is changed update, the UE ID will potentially will change too
                else:
                    ue_id = rnti_id

                # UE already known, update its parameters
                if ue_id in RUNTIME.ues:

                    ue = RUNTIME.ues[ue_id]

                    # RNTI must always be set, but just in case handle the event
                    if option.rnti != 0:
                        ue.rnti = option.rnti
                    else:
                        self.log.info("UE is missing RNTI identifier!")
                        continue

                    # Update the TMSI if has been renew for some reason
                    if option.tmsi != 0:
                        ue.tmsi = option.tmsi

                    # Fill IMSI only if it was not previously set
                    if option.imsi != 0 and ue.imsi != 0:
                        ue.imsi = option.imsi

                    # UE is disconnecting
                    if option.state == 1:
                        RUNTIME.remove_ue(ue_id)

                # UE not known
                else:
                    # Reporting on and entry which switched to offline; ignore
                    if option.state == 1:
                        continue

                    cell = vbs.cells[hdr.cellid]

                    ue = UE(ue_id, option.rnti, option.imsi, option.tmsi,
                            cell, tenant)

                    RUNTIME.ues[ue.ue_id] = ue
                    tenant.ues[ue.ue_id] = ue

                    # UE is connected
                    if option.state == 0:
                        self.server.send_ue_join_message_to_self(ue)

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

        ue.handle_ue_handover_response(origin_vbs, self.vbs, ho.origin_rnti,
                                       ho.target_rnti, ho.origin_pci,
                                       hdr.cellid, event.opcode)

    def _handle_ran_mac_slice_response(self, vbs, hdr, event, msg):
        """Handle an incoming RAN_MAC_SLICE message.
        Args:
            status, a RAN_MAC_SLICE messagge
        Returns:
            None
        """

        dscp = DSCP(msg.dscp)
        plmn_id = PLMNID(msg.plmn_id)

        tenant = RUNTIME.load_tenant_by_plmn_id(plmn_id)

        # check if tenant is valid
        if not tenant:
            self.log.info("Unknown tenant %s", plmn_id)
            return

        # check if slice is valid
        if dscp not in tenant.slices:
            self.log.warning("DSCP %s not found. Removing slice.", dscp)

            cell = vbs.cells[hdr.cellid]
            self.send_del_ran_mac_slice_request(cell, plmn_id, dscp)

            return

        slc = tenant.slices[dscp]

        for raw_cap in msg.options:

            if raw_cap.type not in RAN_MAC_SLICE_TYPES:
                self.log.warning("Unknown options %u", raw_cap.type)
                continue

            prop = RAN_MAC_SLICE_TYPES[raw_cap.type].name
            option = RAN_MAC_SLICE_TYPES[raw_cap.type].parse(raw_cap.data)

            self.log.warning("Processing options %s", prop)

            if raw_cap.type == EP_RAN_MAC_SLICE_SCHED_ID:

                if option.sched_id != slc.lte['static-properties']['sched_id']:

                    if vbs.addr not in slc.lte['vbses']:
                        slc.lte['vbses'][vbs.addr] = {
                            'static-properties': {}
                        }

                    slc.lte['vbses'][vbs.addr] \
                        ['static-properties']['sched_id'] = option.sched_id

            if raw_cap.type == EP_RAN_MAC_SLICE_RBGS:

                if option.rbgs != slc.lte['static-properties']['rbgs']:

                    if vbs.addr not in slc.lte['vbses']:
                        slc.lte['vbses'][vbs.addr] = {
                            'static-properties': {}
                        }

                    slc.lte['vbses'][vbs.addr] \
                        ['static-properties']['rbgs'] = option.rbgs

            if raw_cap.type == EP_RAN_MAC_SLICE_RNTI_LIST:

                rntis = option.rntis

                for ue in list(tenant.ues.values()):

                    if ue.vbs != vbs:
                        continue

                    # if the UE was attached to this slice, but it is not
                    # in the information given by the eNB, it should be
                    # deleted.
                    if slc.dscp == ue.slice and ue.rnti not in rntis:
                        ue.slice = DSCP("0x00")

                    # if the UE was not attached to this slice, but its RNTI
                    # is provided by the eNB for this slice, it should added.
                    elif slc.dscp != ue.slice and ue.rnti in rntis:
                        ue.slice = slc.dscp

        self.log.info("Slice %s updated", slc)

    def send_caps_request(self):
        """Send a CAPS_REQUEST message.
        Args:
            vbs: an VBS object
        Returns:
            None
        """

        msg = Container(length=ENB_CAPS_REQUEST.sizeof(), dummy=0)

        self.send_message(msg,
                          E_TYPE_SINGLE,
                          EP_ACT_CAPS,
                          ENB_CAPS_REQUEST)

    def send_ue_reports_request(self):
        """Send a UE Reports message.
        Args:
            None
        Returns:
            None
        Raises:
            TypeError: if vap is not an VAP object
        """

        msg = Container(length=UE_REPORT_REQUEST.sizeof(), dummy=0)

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

        msg = Container(length=UE_HO_REQUEST.sizeof(),
                        rnti=ue.rnti,
                        target_enbid=b'\x00\x00' + cell.vbs.addr.to_raw(),
                        target_pci=cell.pci,
                        cause=1)

        self.send_message(msg,
                          E_TYPE_SINGLE,
                          EP_ACT_HANDOVER,
                          UE_HO_REQUEST,
                          cellid=ue.cell.pci)

    def send_ran_mac_slice_request(self,
                                   cell_id,
                                   plmn_id=PLMNID(),
                                   dscp=DSCP()):
        """Send a STATUS_SLICE_REQUEST message.
        Args:
            None
        Returns:
            None
        """

        msg = Container(length=RAN_MAC_SLICE_REQUEST.sizeof(),
                        plmn_id=plmn_id.to_raw(),
                        dscp=dscp.to_raw(),
                        padding=b'\x00\x00\x00')

        self.send_message(msg,
                          E_TYPE_SINGLE,
                          EP_ACT_RAN_MAC_SLICE,
                          RAN_MAC_SLICE_REQUEST,
                          cellid=cell_id)

    def send_add_set_ran_mac_slice_request(self, cell, slc, opcode, rntis=[]):
        """Send an SET_RAN_MAC_SLICE_REQUEST message.
        Args:
            None
        Returns:
            None
        Raises:
            None
        """

        sched_id = slc.lte['static-properties']['sched_id']
        rbgs = slc.lte['static-properties']['rbgs']

        if self.vbs.addr in slc.lte['vbses']:

            if 'static-properties' in slc.lte['vbses'][self.vbs.addr]:

                static = slc.lte['vbses'][self.vbs.addr]['static-properties']

                if 'sched_id' in static:
                    sched_id = static['sched_id']

                if 'rbgs' in static:
                    rbgs = static['rbgs']

        msg = Container(plmn_id=slc.tenant.plmn_id.to_raw(),
                        dscp=slc.dscp.to_raw(),
                        padding=b'\x00\x00\x00',
                        options=[])

        # RBGs
        slice_rbgs = Container(rbgs=rbgs)
        s_rbgs = RAN_MAC_SLICE_RBGS.build(slice_rbgs)
        opt_rbgs = Container(type=EP_RAN_MAC_SLICE_RBGS,
                             length=RAN_MAC_SLICE_RBGS.sizeof(),
                             data=s_rbgs)

        # Scheduler id
        slice_sched_id = Container(sched_id=sched_id)
        s_sched_id = RAN_MAC_SLICE_SCHED_ID.build(slice_sched_id)
        opt_sched_id = Container(type=EP_RAN_MAC_SLICE_SCHED_ID,
                                 length=RAN_MAC_SLICE_SCHED_ID.sizeof(),
                                 data=s_sched_id)

        # RNTIs
        slice_rntis = Container(rntis=rntis)
        s_rntis = RAN_MAC_SLICE_RNTI_LIST.build(slice_rntis)
        opt_rntis = Container(type=EP_RAN_MAC_SLICE_RNTI_LIST,
                              length=2*len(rntis),
                              data=s_rntis)

        msg.options = [opt_rbgs, opt_sched_id, opt_rntis]

        msg.length = RAN_MAC_SLICE_REQUEST.sizeof() + \
            opt_rbgs.length + 4 + \
            opt_sched_id.length + 4 + \
            opt_rntis.length + 4

        self.send_message(msg,
                          E_TYPE_SINGLE,
                          EP_ACT_RAN_MAC_SLICE,
                          SET_RAN_MAC_SLICE_REQUEST,
                          opcode=opcode,
                          cellid=cell.pci)

    def send_del_ran_mac_slice_request(self, cell, plmn_id, dscp):
        """Send an DEL_SLICE message. """

        tenant = RUNTIME.load_tenant_by_plmn_id(plmn_id)

        # check if tenant is valid
        if not tenant:
            self.log.info("Unknown tenant %s", plmn_id)
            return

        # check if slice is valid
        if dscp in tenant.slices:
            # UEs already present in the slice must be moved to the default slice
            # before deleting the current slice
            for ue in list(RUNTIME.ues.values()):

                if self.vbs == ue.vbs and dscp == ue.slice:
                    ue.slice = DSCP("0x00")
        else:
            self.log.warning("DSCP %s not found. Removing slice.", dscp)

        # Then proceed to remove the current slice
        msg = Container(plmn_id=plmn_id.to_raw(),
                        dscp=dscp.to_raw(),
                        padding=b'\x00\x00\x00',
                        length=REM_RAN_MAC_SLICE_REQUEST.sizeof())

        self.send_message(msg,
                          E_TYPE_SINGLE,
                          EP_ACT_RAN_MAC_SLICE,
                          REM_RAN_MAC_SLICE_REQUEST,
                          opcode=EP_OPERATION_REM,
                          cellid=cell.pci)
