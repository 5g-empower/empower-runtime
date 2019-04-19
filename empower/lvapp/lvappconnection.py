#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""LVAP Connection."""

import time
import tornado.ioloop
from tornado.iostream import StreamClosedError

from construct import Container

import empower.logger

from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.dpid import DPID
from empower.datatypes.ssid import SSID
from empower.datatypes.dscp import DSCP
from empower.datatypes.ssid import WIFI_NWID_MAXSIZE
from empower.core.resourcepool import ResourceBlock
from empower.core.datapath import Datapath
from empower.core.networkport import NetworkPort
from empower.core.utils import get_xid
from empower.lvapp import HEADER
from empower.lvapp import PT_VERSION
from empower.lvapp import PT_BYE
from empower.lvapp import PT_REGISTER
from empower.lvapp import PT_AUTH_RESPONSE
from empower.lvapp import PT_ASSOC_RESPONSE
from empower.lvapp import PT_SET_TRANSMISSION_POLICY
from empower.lvapp import PT_ADD_LVAP
from empower.lvapp import PT_DEL_LVAP
from empower.lvapp import PT_DEL_TRANSMISSION_POLICY
from empower.lvapp import PT_PROBE_RESPONSE
from empower.lvapp import PT_CAPS_REQUEST
from empower.lvapp import PT_LVAP_STATUS_REQUEST
from empower.lvapp import PT_VAP_STATUS_REQUEST
from empower.lvapp import PT_SET_SLICE
from empower.lvapp import PT_DEL_SLICE
from empower.lvapp import PT_TRANSMISSION_POLICY_STATUS_REQUEST
from empower.lvapp import PT_HELLO
from empower.lvapp import PT_TYPES
from empower.lvapp import PT_DEL_VAP
from empower.lvapp import PT_CAPS_RESPONSE
from empower.lvapp import PT_SLICE_STATUS_REQUEST
from empower.lvapp import PT_ADD_VAP
from empower.core.lvap import LVAP
from empower.core.lvap import PROCESS_RUNNING
from empower.core.vap import VAP
from empower.lvapp import ADD_VAP
from empower.lvapp import DEL_VAP
from empower.lvapp import DEL_LVAP
from empower.lvapp import SET_SLICE
from empower.lvapp import CAPS_REQUEST
from empower.lvapp import LVAP_STATUS_REQUEST
from empower.lvapp import VAP_STATUS_REQUEST
from empower.lvapp import SLICE_STATUS_REQUEST
from empower.lvapp import TRANSMISSION_POLICY_STATUS_REQUEST
from empower.lvapp import PROBE_RESPONSE
from empower.lvapp import AUTH_RESPONSE
from empower.lvapp import ASSOC_RESPONSE
from empower.lvapp import DEL_SLICE
from empower.core.tenant import T_TYPE_SHARED
from empower.core.tenant import T_TYPE_UNIQUE

from empower.main import RUNTIME


class LVAPPConnection:
    """LVAPP Connection.

    Represents a connection to a WTP (Wireless Termination Point) using
    the LVAP Protocol. One LVAPPConnection object is created for every
    WTP in the network. The object implements the logic for handling
    incoming messages. The currently supported messages are:

    Hello. WTP to AC. Used as keepalive between the WTP and the AC

    Probe Request. WTP to AC. Used by the WTP to report about incoming
      probe requests

    Probe Response. AC to WTP. Used by the AC to reply to a probe request.
      Notice that this is needed only the first time a station appears on
      the network.

    Authetication Request. WTP to AC. Used by the WTP to report about
      incoming authentication requests

    Authentication Response. AC to WTP. Used by the AC to reply to an
      authentication request.

    Association Request. WTP to AC. Used by the WTP to report about
      incoming association requests

    Association Response. AC to WTP. Used by the AC to reply to an
      association request.

    Add LVAP. AC to WTP. Used to spawn a new LVAP on a WTP. Notice that
      this happens automatically the first time an WTP reports a probe
      request from a station. Probe requests originated by a station with
      an already defined LVAP will be automatically answered by the WTP
      hosting that LVAP. Other WTPs will report probe requests to the AC
      where they will be silently ignored.

    Attributes:
        stream: The stream object used to talk with the WTP.
        addr: The connection source address, i.e. the WTP IP address.
        server: Pointer to the server object.
        wtp: Pointer to a WTP object.
    """

    def __init__(self, stream, addr, server):
        self.stream = stream
        self.stream.set_nodelay(True)
        self.addr = addr
        self.server = server
        self.wtp = None
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
        """ Check if wtp connection is still active. Disconnect if no hellos
        have been received from the wtp for twice the hello period. """
        if self.wtp and not self.stream.closed():
            timeout = (self.wtp.period / 1000) * 3
            if (self.wtp.last_seen_ts + timeout) < time.time():
                self.log.info('Client inactive %s at %r',
                              self.wtp.addr,
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
            self._trigger_message(hdr.type)
        except Exception as ex:
            self.log.exception(ex)
            self.stream.close()

        if not self.stream.closed():
            self._wait()

    def _trigger_message(self, msg_type):

        if msg_type not in self.server.pt_types:
            self.log.error("Unknown message type %u", msg_type)
            return

        if self.server.pt_types[msg_type]:

            msg_name = self.server.pt_types[msg_type].name

            msg = self.server.pt_types[msg_type].parse(self.__buffer)
            addr = EtherAddress(msg.wtp)

            try:
                wtp = RUNTIME.wtps[addr]
            except KeyError:
                self.log.error("Unknown WTP (%s), closing connection", addr)
                self.stream.close()
                return

            valid = [PT_HELLO]
            if not wtp.connection and msg_type not in valid:
                self.log.info("Got %s message from disconnected %s seq %u",
                              msg_name,
                              EtherAddress(addr),
                              msg.seq)
                return

            self.log.info("Got %s message from %s seq %u",
                          msg_name,
                          EtherAddress(addr),
                          msg.seq)

            valid = [PT_HELLO, PT_CAPS_RESPONSE]
            if not wtp.is_online() and msg_type not in valid:
                self.log.info("WTP %s not ready", wtp.addr)
                return

            handler_name = "_handle_%s" % self.server.pt_types[msg_type].name

            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                handler(wtp, msg)

            if msg_type in self.server.pt_types_handlers:
                for handler in self.server.pt_types_handlers[msg_type]:
                    handler(wtp, msg)

    def _wait(self):
        """ Wait for incoming packets on signalling channel """
        self.__buffer = b''
        future = self.stream.read_bytes(6)
        future.add_done_callback(self._on_read)

    def _on_disconnect(self):
        """ Handle WTP disconnection """

        if not self.wtp:
            return

        self.log.info("WTP disconnected: %s", self.wtp.addr)

        # remove hosted lvaps
        for lvap in list(RUNTIME.lvaps.values()):
            wtps = [x.radio for x in lvap.blocks]
            if self.wtp in wtps:
                RUNTIME.remove_lvap(lvap.addr)

        # remove hosted vaps
        for tenant_id in list(RUNTIME.tenants.keys()):
            for vap_id in list(RUNTIME.tenants[tenant_id].vaps.keys()):
                vap = RUNTIME.tenants[tenant_id].vaps[vap_id]
                if vap.block.radio == self.wtp:
                    self.log.info("Deleting VAP: %s", vap.bssid)
                    del RUNTIME.tenants[tenant_id].vaps[vap.bssid]

        # reset state
        self.wtp.set_disconnected()
        self.wtp.last_seen = 0
        self.wtp.connection = None
        self.wtp.supports = set()
        self.wtp.datapath = None
        self.wtp = None

    def send_message(self, msg_type, msg):
        """Send message and set common parameters."""

        parser = PT_TYPES[msg_type]

        if self.stream.closed():
            self.log.warning("Stream closed, unabled to send %s message to %s",
                             parser.name, self.wtp)
            return 0

        msg.version = PT_VERSION
        msg.seq = self.wtp.seq
        msg.type = msg_type

        self.log.info("Sending %s message to %s seq %u",
                      parser.name,
                      self.wtp,
                      msg.seq)

        self.stream.write(parser.build(msg))

        if hasattr(msg, 'module_id'):
            return msg.module_id

        return 0

    def _handle_add_lvap_response(self, _, status):
        """Handle an incoming ADD_LVAP_RESPONSE message.
        Args:
            status, a ADD_LVAP message
        Returns:
            None
        """

        sta = EtherAddress(status.sta)

        if sta not in RUNTIME.lvaps:
            return

        lvap = RUNTIME.lvaps[sta]

        lvap.handle_add_lvap_response(status.module_id, status.status)

    @classmethod
    def _handle_del_lvap_response(cls, _, status):
        """Handle an incoming DEL_LVAP_RESPONSE message.
        Args:
            status, a DEL_LVAP_RESPONSE message
        Returns:
            None
        """

        sta = EtherAddress(status.sta)

        if sta not in RUNTIME.lvaps:
            return

        lvap = RUNTIME.lvaps[sta]

        lvap.handle_del_lvap_response(status.module_id, status.status)

    def _handle_hello(self, wtp, hello):
        """Handle an incoming HELLO message.
        Args:
            hello, a HELLO message
        Returns:
            None
        """

        # New connection
        if not wtp.connection:

            # set pointer to pnfdev object
            self.wtp = wtp

            # set connection
            wtp.connection = self

            # change state
            wtp.set_connected()

            # send caps request
            self.send_caps_request()

        # Update WTP params
        wtp.period = hello.period
        wtp.last_seen = hello.seq
        wtp.last_seen_ts = time.time()

    def _handle_caps(self, wtp, caps):
        """Handle an incoming CAPS message.
        Args:
            caps, a CAPS message
        Returns:
            None
        """

        dpid = DPID(caps['dpid'])

        if dpid not in RUNTIME.datapaths:
            RUNTIME.datapaths[dpid] = Datapath(dpid)

        wtp.datapath = RUNTIME.datapaths[dpid]

        for block in caps.blocks:
            hwaddr = EtherAddress(block[0])
            r_block = ResourceBlock(wtp, hwaddr, block[1], block[2])
            wtp.supports.add(r_block)

        for port in caps.ports:

            hwaddr = EtherAddress(port[0])
            port_id = int(port[1])
            iface = port[2].decode("utf-8").strip('\0')

            if port_id not in wtp.datapath.network_ports:

                network_port = NetworkPort(dp=wtp.datapath,
                                           port_id=port_id,
                                           hwaddr=hwaddr,
                                           iface=iface)

                wtp.datapath.network_ports[port_id] = network_port

        # set state to online
        wtp.set_online()

        # fetch active lvaps
        self.send_lvap_status_request()

        # fetch active vaps
        self.send_vap_status_request()

        # fetch active traffic rules
        self.send_slice_status_request()

        # fetch active tramission policies
        self.send_transmission_policy_status_request()

        # send vaps
        self.update_vaps()

        # send slices
        self.update_slices()

    def update_vaps(self):
        """Update active VAPs."""

        for tenant in RUNTIME.tenants.values():

            # tenant does not use shared VAPs
            if tenant.bssid_type == T_TYPE_UNIQUE:
                continue

            # wtp not in this tenant
            if self.wtp.addr not in tenant.wtps:
                continue

            for block in self.wtp.supports:

                bssid = tenant.generate_bssid(block.hwaddr)

                # vap has already been created
                if bssid in tenant.vaps:
                    continue

                vap = VAP(bssid, block, tenant)

                self.send_add_vap(vap)
                tenant.vaps[bssid] = vap

    def update_slices(self):
        """Update active Slices."""

        for tenant in RUNTIME.tenants.values():

            # wtp not in this tenant
            if self.wtp.addr not in tenant.wtps:
                continue

            # send slices configuration
            for slc in tenant.slices.values():

                if (not slc.wifi['wtps'] or slc.wifi['wtps'] and
                        self.wtp.addr in slc.wifi['wtps']):

                    for block in self.wtp.supports:
                        self.wtp.connection.send_set_slice(block, slc)

    def _handle_probe_request(self, wtp, request):
        """Handle an incoming PROBE_REQUEST message.
        Args:
            request, a PROBE_REQUEST message
        Returns:
            None
        """

        # Check if block is valid
        valid = wtp.get_block(request.hwaddr, request.channel, request.band)

        if not valid:
            self.log.warning("No valid intersection found. Ignoring request.")
            return

        # check is station is in ACL
        sta = EtherAddress(request.sta)

        if not RUNTIME.is_allowed(sta):
            return

        # Requested BSSID
        incoming_ssid = SSID(request.ssid)

        if incoming_ssid == b'':
            self.log.info("Probe request from %s ssid %s", sta, "Broadcast")
        else:
            self.log.info("Probe request from %s ssid %s", sta, incoming_ssid)

        # generate list of available networks
        networks = list()

        for tenant in RUNTIME.tenants.values():
            if tenant.bssid_type == T_TYPE_SHARED:
                continue
            for wtp_in_tenant in tenant.wtps.values():
                if wtp.addr == wtp_in_tenant.addr:
                    bssid = tenant.generate_bssid(sta)
                    ssid = tenant.tenant_name
                    networks.append((bssid, ssid))

        if not networks:
            self.log.info("No Networks available at this WTP")
            return

        # If lvap does not exist then create it. Otherwise just refresh list
        # of networks
        if sta not in RUNTIME.lvaps:

            # spawn new LVAP
            self.log.info("Spawning new LVAP %s on %s", sta, wtp.addr)

            assoc_id = RUNTIME.assoc_id()

            lvap = LVAP(sta, assoc_id=assoc_id)
            lvap.networks = networks
            lvap.supported_band = request.supported_band

            # this will trigger an LVAP ADD message
            lvap.blocks = valid[0]

            # save LVAP in the runtime
            RUNTIME.lvaps[sta] = lvap

            # Send probe response
            self.send_probe_response(lvap, incoming_ssid)

            return

        # Update networks
        lvap = RUNTIME.lvaps[sta]
        lvap.networks = networks
        lvap.commit()

        # Send probe response
        if lvap.wtp == wtp:
            self.send_probe_response(lvap, incoming_ssid)

    def _handle_auth_request(self, wtp, request):
        """Handle an incoming AUTH_REQUEST message.
        Args:
            request, a AUTH_REQUEST message
        Returns:
            None
        """

        sta = EtherAddress(request.sta)

        if sta not in RUNTIME.lvaps:
            self.log.info("Auth request from unknown LVAP %s", sta)
            return

        lvap = RUNTIME.lvaps[sta]

        incoming_bssid = EtherAddress(request.bssid)

        # The request bssid is the lvap current bssid, then just reply
        if lvap.bssid == incoming_bssid:
            lvap.bssid = incoming_bssid
            lvap.authentication_state = True
            lvap.association_state = False
            lvap.ssid = None
            lvap.commit()
            self.send_auth_response(lvap)
            return

        # Otherwise check if the requested BSSID belongs to a unique tenant
        for tenant in RUNTIME.tenants.values():

            if tenant.bssid_type == T_TYPE_SHARED:
                continue

            bssid = tenant.generate_bssid(lvap.addr)

            if bssid == incoming_bssid:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = False
                lvap.ssid = None
                lvap.commit()
                self.send_auth_response(lvap)
                return

        # Finally check if this is a shared bssid
        for tenant in RUNTIME.tenants.values():

            if tenant.bssid_type == T_TYPE_UNIQUE:
                continue

            if incoming_bssid in tenant.vaps:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = False
                lvap.ssid = None
                lvap.commit()
                self.send_auth_response(lvap)
                return

        self.log.info("Auth request from unknown BSSID %s", incoming_bssid)

    def _handle_assoc_request(self, wtp, request):
        """Handle an incoming ASSOC_REQUEST message.
        Args:
            request, a ASSOC_REQUEST message
        Returns:
            None
        """

        sta = EtherAddress(request.sta)

        if sta not in RUNTIME.lvaps:
            self.log.info("Assoc request from unknown LVAP %s", sta)
            return

        lvap = RUNTIME.lvaps[sta]

        incoming_bssid = EtherAddress(request.bssid)

        if lvap.bssid != incoming_bssid:
            self.log.info("Assoc request for invalid BSSID %s", incoming_bssid)
            return

        incoming_ssid = SSID(request.ssid)

        # Check if the requested SSID is from a unique tenant
        for tenant in RUNTIME.tenants.values():

            if tenant.bssid_type == T_TYPE_SHARED:
                continue

            bssid = tenant.generate_bssid(lvap.addr)

            if bssid != incoming_bssid:
                self.log.info("Invalid BSSID %s", incoming_bssid)
                continue

            if tenant.tenant_name == incoming_ssid:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = True
                lvap.ssid = incoming_ssid
                lvap.supported_band = request.supported_band
                lvap.commit()
                self.send_assoc_response(lvap)
                return

        # Check if the requested SSID is from a unique tenant
        for tenant in RUNTIME.tenants.values():

            if tenant.bssid_type == T_TYPE_UNIQUE:
                continue

            if incoming_bssid not in tenant.vaps:
                self.log.info("Invalid BSSID %s", incoming_bssid)
                continue

            ssid = tenant.vaps[incoming_bssid].ssid

            if ssid == incoming_ssid:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = True
                lvap.ssid = incoming_ssid
                lvap.supported_band = request.supported_band
                lvap.commit()
                self.send_assoc_response(lvap)
                return

        self.log.info("Unable to find SSID %s", incoming_ssid)

    def _handle_status_lvap(self, wtp, status):
        """Handle an incoming STATUS_LVAP message.
        Args:
            status, a STATUS_LVAP message
        Returns:
            None
        """

        sta = EtherAddress(status.sta)

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found. Removing block.")
            wtp.connection.send_del_lvap(sta)
            return

        # If the LVAP does not exists, then create a new one
        if sta not in RUNTIME.lvaps:
            RUNTIME.lvaps[sta] = LVAP(sta,
                                      assoc_id=status.assoc_id,
                                      state=PROCESS_RUNNING)

        lvap = RUNTIME.lvaps[sta]

        # update LVAP params
        lvap.supported_band = status.supported_band
        lvap.encap = EtherAddress(status.encap)
        lvap.authentication_state = bool(status.flags.authenticated)
        lvap.association_state = bool(status.flags.associated)

        ssid = SSID(status.ssid)
        if ssid == SSID():
            ssid = None

        bssid = EtherAddress(status.bssid)
        if bssid == EtherAddress("00:00:00:00:00:00"):
            bssid = None

        lvap.bssid = bssid

        set_mask = status.flags.set_mask

        # received downlink block but a different downlink block is already
        # present, delete before going any further
        if set_mask and lvap.blocks[0] and lvap.blocks[0] != valid[0]:
            lvap.blocks[0].radio.connection.send_del_lvap(sta)

        if set_mask:
            lvap._downlink = valid[0]
        else:
            lvap._uplink.append(valid[0])

        # if this is not a DL+UL block then stop here
        if not set_mask:
            return

        # if an SSID is set and the incoming SSID is different from the
        # current one then raise an LVAP leave event and remove LVAP from the
        # current SSID
        if lvap.ssid and ssid != lvap.ssid:
            self.server.send_lvap_leave_message_to_self(lvap)
            del lvap.tenant.lvaps[lvap.addr]
            lvap.ssid = None

        # if the incoming ssid is not none then raise an lvap join event
        if ssid:
            lvap.ssid = ssid
            lvap.tenant.lvaps[lvap.addr] = lvap
            self.server.send_lvap_join_message_to_self(lvap)

        # udpate networks
        networks = list()

        for network in status.networks:
            incoming = (EtherAddress(network.bssid), SSID(network.ssid))
            networks.append(incoming)

        lvap.networks = networks

        self.log.info("LVAP status %s", lvap)

    def _handle_status_transmission_policy(self, wtp, status):
        """Handle an incoming TRANSMISSION_POLICY message.
        Args:
            status, a TRANSMISSION_POLICY message
        Returns:
            None
        """

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found. Removing block.")
            return

        sta = EtherAddress(status.sta)
        tx_policy = valid[0].tx_policies[sta]

        tx_policy.set_mcs([float(x) / 2 for x in status.mcs])
        tx_policy.set_ht_mcs([int(x) for x in status.ht_mcs])
        tx_policy.set_rts_cts(status.rts_cts)
        tx_policy.set_mcast(status.tx_mcast)
        tx_policy.set_ur_count(status.ur_mcast_count)
        tx_policy.set_no_ack(status.flags.no_ack)

        self.log.info("Tranmission policy status %s", tx_policy)

    def _handle_status_slice(self, wtp, status):
        """Handle an incoming STATUS_SLICE message.
        Args:
            status, a STATUS_SLICE message
        Returns:
            None
        """

        dscp = DSCP(status.dscp)
        ssid = SSID(status.ssid)

        tenant = RUNTIME.load_tenant(ssid)

        if not tenant:
            self.log.info("Slice status from unknown tenant %s", ssid)
            return

        if not wtp.is_online():
            return

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found.")
            return

        # check if slice is valid
        if dscp not in tenant.slices:
            self.log.warning("DSCP %s not found. Removing slice.", dscp)
            self.send_del_slice(valid[0], ssid, dscp)
            return

        slc = tenant.slices[dscp]
        prop = slc.wifi['static-properties']

        if prop['quantum'] != status.quantum:
            if wtp.addr not in slc.wifi['wtps']:
                slc.wifi['wtps'][wtp.addr] = {'static-properties': {}}
            slc.wifi['wtps'][wtp.addr]['static-properties']['quantum'] = status.quantum

        if prop['amsdu_aggregation'] != bool(status.flags.amsdu_aggregation):

            if wtp.addr not in slc.wifi['wtps']:
                slc.wifi['wtps'][wtp.addr] = {'static-properties': {}}
            slc.wifi['wtps'][wtp.addr]['static-properties']['amsdu_aggregation'] = \
                bool(status.flags.amsdu_aggregation)

        if prop['scheduler'] != status.scheduler:
            if wtp.addr not in slc.wifi['wtps']:
                slc.wifi['wtps'][wtp.addr] = {'static-properties': {}}
            slc.wifi['wtps'][wtp.addr]['static-properties']['scheduler'] = status.scheduler

        self.log.info("Slice %s updated", slc)

    def _handle_status_vap(self, wtp, status):
        """Handle an incoming STATUS_VAP message.
        Args:
            status, a STATUS_VAP message
        Returns:
            None
        """

        bssid = EtherAddress(status.bssid)
        ssid = SSID(status.ssid)
        tenant = RUNTIME.load_tenant(ssid)

        if not tenant:
            self.log.info("VAP %s from unknown tenant %s", bssid, ssid)
            return

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found. Removing VAP.")
            wtp.connection.send_del_vap(bssid)
            return

        # If the VAP does not exists, then create a new one
        if bssid not in tenant.vaps:
            vap = VAP(bssid, valid, tenant)
            tenant.vaps[bssid] = vap

        vap = tenant.vaps[bssid]

        self.log.info("VAP status %s", vap)

    def send_caps_request(self):
        """Send a CAPS_REQUEST message."""

        msg = Container(length=CAPS_REQUEST.sizeof())
        return self.send_message(PT_CAPS_REQUEST, msg)

    def send_lvap_status_request(self):
        """Send a LVAP_STATUS_REQUEST message."""

        msg = Container(length=LVAP_STATUS_REQUEST.sizeof())
        return self.send_message(PT_LVAP_STATUS_REQUEST, msg)

    def send_vap_status_request(self):
        """Send a VAP_STATUS_REQUEST message."""

        msg = Container(length=VAP_STATUS_REQUEST.sizeof())
        return self.send_message(PT_VAP_STATUS_REQUEST, msg)

    def send_slice_status_request(self):
        """Send a PT_SLICE_STATUS_REQUEST message."""

        msg = Container(length=SLICE_STATUS_REQUEST.sizeof())
        return self.send_message(PT_SLICE_STATUS_REQUEST, msg)

    def send_transmission_policy_status_request(self):
        """Send a TRANSMISSION_POLICY_STATUS_REQUEST message."""

        msg = Container(length=TRANSMISSION_POLICY_STATUS_REQUEST.sizeof())
        return self.send_message(PT_TRANSMISSION_POLICY_STATUS_REQUEST, msg)

    def send_add_vap(self, vap):
        """Send a ADD_VAP message."""

        msg = Container(length=ADD_VAP.sizeof(),
                        hwaddr=vap.block.hwaddr.to_raw(),
                        channel=vap.block.channel,
                        band=vap.block.band,
                        bssid=vap.bssid.to_raw(),
                        ssid=vap.ssid.to_raw())

        return self.send_message(PT_ADD_VAP, msg)

    def send_del_vap(self, bssid):
        """Send a DEL_VAP message."""

        msg = Container(length=DEL_VAP.sizeof(), bssid=bssid.to_raw())
        return self.send_message(PT_DEL_VAP, msg)

    def send_assoc_response(self, lvap):
        """Send a ASSOC_RESPONSE message."""

        msg = Container(length=ASSOC_RESPONSE.sizeof(),
                        sta=lvap.addr.to_raw())
        return self.send_message(PT_ASSOC_RESPONSE, msg)

    def send_auth_response(self, lvap):
        """Send a AUTH_RESPONSE message."""

        msg = Container(length=AUTH_RESPONSE.sizeof(),
                        sta=lvap.addr.to_raw(),
                        bssid=lvap.bssid.to_raw())

        return self.send_message(PT_AUTH_RESPONSE, msg)

    def send_probe_response(self, lvap, ssid):
        """Send a PROBE_RESPONSE message."""

        msg = Container(length=PROBE_RESPONSE.sizeof(),
                        sta=lvap.addr.to_raw(),
                        ssid=ssid.to_raw())

        return self.send_message(PT_PROBE_RESPONSE, msg)

    def send_del_lvap(self, sta, csa_switch_channel=0):
        """Send a DEL_LVAP message."""

        msg = Container(length=DEL_LVAP.sizeof(),
                        module_id=get_xid(),
                        sta=sta.to_raw(),
                        csa_switch_mode=0,
                        csa_switch_count=3,
                        csa_switch_channel=csa_switch_channel)

        return self.send_message(PT_DEL_LVAP, msg)

    def send_set_transmission_policy(self, tx_policy):
        """Send a SET_TRANSMISSION_POLICY message."""

        flags = Container(no_ack=tx_policy.no_ack)
        rates = sorted([int(x * 2) for x in tx_policy.mcs])
        ht_rates = sorted([int(x) for x in tx_policy.ht_mcs])

        msg = Container(length=32 + len(rates) + len(ht_rates),
                        flags=flags,
                        sta=tx_policy.addr.to_raw(),
                        hwaddr=tx_policy.block.hwaddr.to_raw(),
                        channel=tx_policy.block.channel,
                        band=tx_policy.block.band,
                        rts_cts=tx_policy.rts_cts,
                        tx_mcast=tx_policy.mcast,
                        ur_mcast_count=tx_policy.ur_count,
                        nb_mcses=len(rates),
                        nb_ht_mcses=len(ht_rates),
                        mcs=rates,
                        ht_mcs=ht_rates)

        return self.send_message(PT_SET_TRANSMISSION_POLICY, msg)

    def send_del_transmission_policy(self, tx_policy):
        """Send a DEL_TRANSMISSION_POLICY message."""

        msg = Container(length=24,
                        sta=tx_policy.addr.to_raw(),
                        hwaddr=tx_policy.block.hwaddr.to_raw(),
                        channel=tx_policy.block.channel,
                        band=tx_policy.block.band)

        return self.send_message(PT_DEL_TRANSMISSION_POLICY, msg)

    def send_add_lvap(self, lvap, block, set_mask):
        """Send a ADD_LVAP message."""

        flags = Container(authenticated=lvap.authentication_state,
                          associated=lvap.association_state,
                          set_mask=set_mask)

        encap = EtherAddress("00:00:00:00:00:00")
        if lvap.encap:
            encap = lvap.encap

        bssid = EtherAddress()
        if lvap.bssid:
            bssid = lvap.bssid

        ssid = SSID()
        if lvap.ssid:
            ssid = lvap.ssid

        msg = Container(length=78,
                        flags=flags,
                        assoc_id=lvap.assoc_id,
                        module_id=get_xid(),
                        hwaddr=block.hwaddr.to_raw(),
                        channel=block.channel,
                        band=block.band,
                        supported_band=lvap.supported_band,
                        sta=lvap.addr.to_raw(),
                        encap=encap.to_raw(),
                        bssid=bssid.to_raw(),
                        ssid=ssid.to_raw(),
                        networks=[])

        for network in lvap.networks:
            msg.length = msg.length + 6 + WIFI_NWID_MAXSIZE + 1
            msg.networks.append(Container(bssid=network[0].to_raw(),
                                          ssid=network[1].to_raw()))

        xid = self.send_message(PT_ADD_LVAP, msg)

        lvap.pending.append(xid)

    def send_bye_message_to_self(self):
        """Send a unsollicited BYE message to senf."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.wtp_down(self.wtp)

        for handler in self.server.pt_types_handlers[PT_BYE]:
            handler(self.wtp)

    def send_register_message_to_self(self):
        """Send a unsollicited REGISTER message to senf."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.wtp_up(self.wtp)

        for handler in self.server.pt_types_handlers[PT_REGISTER]:
            handler(self.wtp)

    def send_set_slice(self, block, slc):
        """Send an SET_SLICE message."""

        ssid = slc.tenant.tenant_name

        amsdu_aggregation = slc.wifi['static-properties']['amsdu_aggregation']
        quantum = slc.wifi['static-properties']['quantum']
        scheduler = slc.wifi['static-properties']['scheduler']

        if self.wtp.addr in slc.wifi['wtps']:

            static = slc.wifi['wtps'][self.wtp.addr]['static-properties']

            if 'amsdu_aggregation' in static:
                amsdu_aggregation = static['amsdu_aggregation']

            if 'quantum' in static:
                quantum = static['quantum']

            if 'scheduler' in static:
                scheduler = static['scheduler']

        flags = Container(amsdu_aggregation=amsdu_aggregation)

        msg = Container(length=SET_SLICE.sizeof(),
                        flags=flags,
                        hwaddr=block.hwaddr.to_raw(),
                        channel=block.channel,
                        band=block.band,
                        quantum=quantum,
                        scheduler=scheduler,
                        dscp=slc.dscp.to_raw(),
                        ssid=ssid.to_raw())

        return self.send_message(PT_SET_SLICE, msg)

    def send_del_slice(self, block, ssid, dscp):
        """Send an DEL_SLICEs message. """

        msg = Container(length=DEL_SLICE.sizeof(),
                        hwaddr=block.hwaddr.to_raw(),
                        channel=block.channel,
                        band=block.band,
                        dscp=dscp.to_raw(),
                        ssid=ssid.to_raw())

        return self.send_message(PT_DEL_SLICE, msg)
