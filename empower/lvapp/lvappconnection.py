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

from construct import Container

import empower.logger

from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.dpid import DPID
from empower.datatypes.ssid import SSID
from empower.datatypes.dscp import DSCP
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
from empower.lvapp import PT_SET_PORT
from empower.lvapp import PT_ADD_LVAP
from empower.lvapp import PT_DEL_LVAP
from empower.lvapp import PT_DEL_PORT
from empower.lvapp import PT_PROBE_RESPONSE
from empower.lvapp import PT_CAPS_REQUEST
from empower.lvapp import PT_LVAP_STATUS_REQUEST
from empower.lvapp import PT_VAP_STATUS_REQUEST
from empower.lvapp import PT_SET_TRAFFIC_RULE_QUEUE
from empower.lvapp import PT_DEL_TRAFFIC_RULE_QUEUE
from empower.lvapp import PT_PORT_STATUS_REQUEST
from empower.lvapp import PT_HELLO
from empower.lvapp import PT_TYPES
from empower.lvapp import PT_DEL_VAP
from empower.lvapp import PT_CAPS_RESPONSE
from empower.lvapp import PT_TRAFFIC_RULE_QUEUE_STATUS_REQUEST
from empower.core.lvap import LVAP
from empower.core.lvap import PROCESS_RUNNING
from empower.core.vap import VAP
from empower.lvapp import PT_ADD_VAP
from empower.core.tenant import T_TYPE_SHARED
from empower.core.tenant import T_TYPE_UNIQUE
from empower.core.utils import generate_bssid

from empower.main import RUNTIME


BASE_MAC = EtherAddress("02:ca:fe:00:00:00")


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
        address: The connection source address, i.e. the WTP IP address.
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
        self.stream.read_bytes(6, self._on_read)

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
        for tenant_id in RUNTIME.tenants.keys():
            for vap_id in list(RUNTIME.tenants[tenant_id].vaps.keys()):
                vap = RUNTIME.tenants[tenant_id].vaps[vap_id]
                if vap.wtp == self.wtp:
                    self.log.info("Deleting VAP: %s", vap.net_bssid)
                    del RUNTIME.tenants[tenant_id].vaps[vap.net_bssid]

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

    @classmethod
    def _handle_add_lvap_response(cls, _, status):
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
        self.send_traffic_rule_queue_status_request()

        # fetch active transmission rules
        self.send_port_status_request()

        # send vaps
        for tenant in RUNTIME.tenants.values():

            # tenant does not use shared VAPs
            if tenant.bssid_type == T_TYPE_UNIQUE:
                continue

            # wtp not in this tenant
            if self.wtp.addr not in tenant.wtps:
                continue

            tenant_id = tenant.tenant_id
            tokens = [tenant_id.hex[0:12][i:i + 2] for i in range(0, 12, 2)]
            base_bssid = EtherAddress(':'.join(tokens))

            for block in self.wtp.supports:

                net_bssid = generate_bssid(base_bssid, block.hwaddr)

                # vap has already been created
                if net_bssid in RUNTIME.tenants[tenant_id].vaps:
                    continue

                vap = VAP(net_bssid, block, self.wtp, tenant)

                self.send_add_vap(vap)
                RUNTIME.tenants[tenant_id].vaps[net_bssid] = vap

        # send traffic rule queues
        for tenant in RUNTIME.tenants.values():
            for rule in tenant.traffic_rule_queues:
                tenant.dispach_traffic_rule_queue(rule)

    def _handle_probe_request(self, wtp, request):
        """Handle an incoming PROBE_REQUEST message.
        Args:
            request, a PROBE_REQUEST message
        Returns:
            None
        """

        sta = EtherAddress(request.sta)

        if sta in RUNTIME.lvaps:
            return

        if not RUNTIME.is_allowed(sta):
            return

        ssid = SSID(request.ssid)

        if request.ssid == b'':
            self.log.info("Probe request from %s ssid %s", sta, "Broadcast")
        else:
            self.log.info("Probe request from %s ssid %s", sta, ssid)

        # generate list of available SSIDs
        ssids = set()

        for tenant in RUNTIME.tenants.values():
            if tenant.bssid_type == T_TYPE_SHARED:
                continue
            for wtp_in_tenant in tenant.wtps.values():
                if wtp.addr == wtp_in_tenant.addr:
                    ssids.add(tenant.tenant_name)

        if not ssids:
            self.log.info("No SSIDs available at this WTP")
            return

        # check if block is valid
        net_bssid = generate_bssid(BASE_MAC, sta)
        lvap = LVAP(sta, net_bssid, net_bssid)
        lvap._ssids = list(ssids)

        # set supported band
        lvap._supported_band = request.supported_band

        # Check if block is valid
        valid = wtp.get_block(request.hwaddr, request.channel, request.band)

        if not valid:
            self.log.warning("No valid intersection found. Ignoring request.")
            return

        # spawn new LVAP
        self.log.info("Spawning new LVAP %s on %s", sta, wtp.addr)

        # this will trigger an LVAP ADD message
        lvap.blocks = valid[0]

        # save LVAP in the runtime
        RUNTIME.lvaps[sta] = lvap

    def _handle_auth_request(self, wtp, request):
        """Handle an incoming AUTH_REQUEST message.
        Args:
            request, a AUTH_REQUEST message
        Returns:
            None
        """

        sta = EtherAddress(request.sta)
        bssid = EtherAddress(request.bssid)

        if sta not in RUNTIME.lvaps:
            self.log.info("Auth request from unknown LVAP %s", sta)
            return

        lvap = RUNTIME.lvaps[sta]

        if not RUNTIME.is_allowed(sta):
            return

        lvap_bssid = None

        # the request bssid is the lvap's unique bssid
        if lvap.net_bssid == bssid:

            lvap_bssid = lvap.net_bssid

        # else if is a shared bssid
        else:

            shared_tenants = [x for x in RUNTIME.tenants.values()
                              if x.bssid_type == T_TYPE_SHARED]

            wtp = RUNTIME.wtps[wtp.addr]

            # look for bssid in shared tenants
            for tenant in shared_tenants:
                if bssid in tenant.vaps and tenant.vaps[bssid].wtp == wtp:
                    lvap_bssid = bssid
                    break

        # invalid bssid, ignore request
        if not lvap_bssid:
            return

        # this will trigger an add lvap message to update the bssid
        lvap.lvap_bssid = lvap_bssid

        self.send_auth_response(lvap)

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

        if not RUNTIME.is_allowed(sta):
            return

        ssid = SSID(request.ssid.decode('UTF-8'))
        bssid = EtherAddress(request.bssid)

        tenant_name = None

        # look for ssid in shared tenants
        for tenant_id in RUNTIME.tenants:

            tenant = RUNTIME.tenants[tenant_id]

            if tenant.bssid_type == T_TYPE_UNIQUE:
                continue

            if bssid in tenant.vaps and ssid == tenant.tenant_name:
                tenant_name = tenant.tenant_name

        # otherwise this must be the lvap unique bssid
        if lvap.net_bssid == bssid and ssid in lvap.ssids:
            tenant_name = ssid

        if not tenant_name:
            return

        # update some LVAP fields
        lvap.tenant = RUNTIME.load_tenant(tenant_name)
        lvap.assoc_id = self.server.assoc_id
        lvap.supported_band = request.supported_band

        self.send_assoc_response(lvap)

    def _handle_status_lvap(self, wtp, status):
        """Handle an incoming STATUS_LVAP message.
        Args:
            status, a STATUS_LVAP message
        Returns:
            None
        """

        sta = EtherAddress(status.sta)

        # If the LVAP does not exists, then create a new one
        if sta not in RUNTIME.lvaps:

            net_bssid_addr = EtherAddress(status.net_bssid)
            lvap_bssid_addr = EtherAddress(status.lvap_bssid)
            lvap = LVAP(sta, net_bssid_addr, lvap_bssid_addr)
            lvap._state = PROCESS_RUNNING

            RUNTIME.lvaps[sta] = lvap

        lvap = RUNTIME.lvaps[sta]

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found. Removing block.")
            wtp.connection.send_del_lvap(lvap)
            return

        set_mask = bool(status.flags.set_mask)

        # received downlink block but a different downlink block is already
        # present, delete before going any further
        if set_mask and lvap._downlink and lvap._downlink != valid[0]:
            lvap._downlink.radio.connection.send_del_lvap(lvap)

        if set_mask:
            lvap._downlink = valid[0]
        else:
            lvap._uplink.append(valid[0])

        # set supported band
        lvap._supported_band = status.supported_band

        # update LVAP params
        lvap.authentication_state = bool(status.flags.authenticated)
        lvap.association_state = bool(status.flags.associated)

        lvap._assoc_id = status.assoc_id
        lvap._encap = EtherAddress(status.encap)
        ssids = [SSID(x.ssid) for x in status.ssids]

        # update ssid
        if lvap.ssid:

            # Raise LVAP leave event
            self.server.send_lvap_leave_message_to_self(lvap)

            # removing LVAP from tenant, need first to look for right tenant
            if lvap.addr in lvap.tenant.lvaps:
                self.log.info("Removing %s from tenant %s",
                              lvap.addr, lvap.ssid)
                del lvap.tenant.lvaps[lvap.addr]

            lvap._tenant = None

        # update remaining ssids
        lvap._ssids = ssids[1:]

        if ssids[0]:

            tenant = RUNTIME.load_tenant(ssids[0])

            if not tenant:
                self.log.info("LVAP %s from unknown tenant %s",
                              lvap.addr, ssids[0])
                RUNTIME.remove_lvap(lvap.addr)
                return

            # setting tenant without seding out add lvap message
            lvap._tenant = tenant

            # adding LVAP to tenant
            self.log.info("Adding %s to tenant %s", lvap.addr, ssids[0])
            lvap.tenant.lvaps[lvap.addr] = lvap

            # Raise LVAP join event
            self.server.send_lvap_join_message_to_self(lvap)

        self.log.info("LVAP status %s", lvap)

    def _handle_status_port(self, wtp, status):
        """Handle an incoming PORT message.
        Args:
            status, a STATUS_PORT message
        Returns:
            None
        """

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found. Removing block.")
            wtp.connection.send_del_lvap(lvap)
            return

        sta = EtherAddress(status.sta)
        tx_policy = valid[0].tx_policies[sta]

        tx_policy._mcs = set([float(x) / 2 for x in status.mcs])
        tx_policy._ht_mcs = set([int(x) for x in status.ht_mcs])
        tx_policy._rts_cts = int(status.rts_cts)
        tx_policy._mcast = int(status.tx_mcast)
        tx_policy._ur_count = int(status.ur_mcast_count)
        tx_policy._no_ack = bool(status.flags.no_ack)

        self.log.info("Port status %s", tx_policy)

    def _handle_status_traffic_rule_queue(self, wtp, status):
        """Handle an incoming STATUS_TRAFFIC_RULE_QUEUE message.
        Args:
            status, a STATUS_TRAFFIC_RULE_QUEUE message
        Returns:
            None
        """

        quantum = status.quantum
        amsdu_aggregation = bool(status.flags.amsdu_aggregation)
        dscp = DSCP(status.dscp)
        ssid = SSID(status.ssid)

        tenant = RUNTIME.load_tenant(ssid)

        if not tenant:
            self.log.info("Traffic rule status from unknown tenant %s", ssid)
            return

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found. Removing block.")
            wtp.connection.send_del_lvap(lvap)
            return

        trq = valid[0].traffic_rule_queues[(ssid, dscp)]

        trq._quantum = quantum
        trq._amsdu_aggregation = amsdu_aggregation

        self.log.info("Transmission rule status %s", trq)

    def _handle_status_vap(self, wtp, status):
        """Handle an incoming STATUS_VAP message.
        Args:
            status, a STATUS_VAP message
        Returns:
            None
        """

        net_bssid_addr = EtherAddress(status.net_bssid)
        ssid = SSID(status.ssid)
        tenant = RUNTIME.load_tenant(ssid)

        if not tenant:
            self.log.info("VAP %s from unknown tenant %s",
                          net_bssid_addr, ssid)
            return

        # Check if block is valid
        valid = wtp.get_block(status.hwaddr, status.channel, status.band)

        if not valid:
            self.log.warning("No valid intersection found. Removing VAP.")
            wtp.connection.send_del_vap(net_bssid_addr)
            return

        # If the VAP does not exists, then create a new one
        if net_bssid_addr not in tenant.vaps:
            vap = VAP(net_bssid_addr, valid, wtp, tenant)
            tenant.vaps[net_bssid_addr] = vap

        vap = tenant.vaps[net_bssid_addr]

        self.log.info("VAP status %s", vap)

    def send_caps_request(self):
        """Send a CAPS_REQUEST message."""

        msg = Container(length=10)
        return self.send_message(PT_CAPS_REQUEST, msg)

    def send_lvap_status_request(self):
        """Send a LVAP_STATUS_REQUEST message."""

        msg = Container(length=10)
        return self.send_message(PT_LVAP_STATUS_REQUEST, msg)

    def send_vap_status_request(self):
        """Send a VAP_STATUS_REQUEST message."""

        msg = Container(length=10)
        return self.send_message(PT_VAP_STATUS_REQUEST, msg)

    def send_traffic_rule_queue_status_request(self):
        """Send a PT_TRAFFIC_RULE_QUEUE_STATUS_REQUEST message."""

        msg = Container(length=10)
        return self.send_message(PT_TRAFFIC_RULE_QUEUE_STATUS_REQUEST, msg)

    def send_port_status_request(self):
        """Send a PORT_STATUS_REQUEST message."""

        msg = Container(length=10)
        return self.send_message(PT_PORT_STATUS_REQUEST, msg)

    def send_add_vap(self, vap):
        """Send a ADD_VAP message."""

        msg = Container(length=24 + len(vap.ssid),
                        hwaddr=vap.block.hwaddr.to_raw(),
                        channel=vap.block.channel,
                        band=vap.block.band,
                        net_bssid=vap.net_bssid.to_raw(),
                        ssid=vap.ssid.to_raw())

        return self.send_message(PT_ADD_VAP, msg)

    def send_del_vap(self, net_bssid):
        """Send a DEL_VAP message."""

        msg = Container(length=16, net_bssid=net_bssid.to_raw())
        return self.send_message(PT_DEL_VAP, msg)

    def send_assoc_response(self, lvap):
        """Send a ASSOC_RESPONSE message."""

        msg = Container(length=16, sta=lvap.addr.to_raw())
        return self.send_message(PT_ASSOC_RESPONSE, msg)

    def send_auth_response(self, lvap):
        """Send a AUTH_RESPONSE message."""

        msg = Container(length=22,
                        sta=lvap.addr.to_raw(),
                        bssid=lvap.lvap_bssid.to_raw())

        return self.send_message(PT_AUTH_RESPONSE, msg)

    def send_probe_response(self, lvap, ssid):
        """Send a PROBE_RESPONSE message."""

        msg = Container(length=16 + len(ssid.to_raw()),
                        sta=lvap.addr.to_raw(),
                        ssid=ssid.to_raw())

        return self.send_message(PT_PROBE_RESPONSE, msg)

    def send_del_lvap(self, lvap, csa_switch_channel=0):
        """Send a DEL_LVAP message."""

        msg = Container(length=23,
                        module_id=get_xid(),
                        sta=lvap.addr.to_raw(),
                        csa_switch_mode=0,
                        csa_switch_count=3,
                        csa_switch_channel=csa_switch_channel)

        return self.send_message(PT_DEL_LVAP, msg)

    def send_set_port(self, tx_policy):
        """Send a SET_PORT message."""

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

        return self.send_message(PT_SET_PORT, msg)

    def send_del_port(self, tx_policy):
        """Send a DEL_PORT message."""

        msg = Container(length=24,
                        sta=tx_policy.addr.to_raw(),
                        hwaddr=tx_policy.block.hwaddr.to_raw(),
                        channel=tx_policy.block.channel,
                        band=tx_policy.block.band)

        return self.send_message(PT_DEL_PORT, msg)

    def send_add_lvap(self, lvap, block, set_mask):
        """Send a ADD_LVAP message."""

        flags = Container(authenticated=lvap.authentication_state,
                          associated=lvap.association_state,
                          set_mask=set_mask)

        encap = EtherAddress("00:00:00:00:00:00")

        if lvap.encap:
            encap = lvap.encap

        msg = Container(length=51,
                        flags=flags,
                        assoc_id=lvap.assoc_id,
                        module_id=get_xid(),
                        hwaddr=block.hwaddr.to_raw(),
                        channel=block.channel,
                        band=block.band,
                        supported_band=lvap.supported_band,
                        sta=lvap.addr.to_raw(),
                        encap=encap.to_raw(),
                        net_bssid=lvap.net_bssid.to_raw(),
                        lvap_bssid=lvap.lvap_bssid.to_raw(),
                        ssids=[])

        if lvap.ssid:
            b_ssid = lvap.ssid.to_raw()
            tmp = Container(length=len(b_ssid), ssid=b_ssid)
            msg.ssids.append(tmp)
            msg.length = msg.length + len(b_ssid) + 1
        else:
            msg.ssids.append(Container(length=0, ssid=b''))
            msg.length = msg.length + 1

        for ssid in lvap.ssids:
            b_ssid = ssid.to_raw()
            tmp = Container(length=len(b_ssid), ssid=b_ssid)
            msg.ssids.append(tmp)
            msg.length = msg.length + len(b_ssid) + 1

        return self.send_message(PT_ADD_LVAP, msg)

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

    def send_set_traffic_rule_queue(self, traffic_rule):
        """Send an SET_TRAFFIC_RULE message."""

        flags = Container(amsdu_aggregation=traffic_rule.amsdu_aggregation)

        msg = Container(length=25 + len(traffic_rule.ssid),
                        flags=flags,
                        hwaddr=traffic_rule.block.hwaddr.to_raw(),
                        channel=traffic_rule.block.channel,
                        band=traffic_rule.block.band,
                        quantum=traffic_rule.quantum,
                        dscp=traffic_rule.dscp.to_raw(),
                        ssid=traffic_rule.ssid.to_raw())

        return self.send_message(PT_SET_TRAFFIC_RULE_QUEUE, msg)

    def send_del_traffic_rule_queue(self, traffic_rule):
        """Send an DEL_TRAFFIC_RULE message. """

        msg = Container(length=19 + len(traffic_rule.ssid),
                        hwaddr=traffic_rule.block.hwaddr.to_raw(),
                        channel=traffic_rule.block.channel,
                        band=traffic_rule.block.band,
                        dscp=traffic_rule.dscp.to_raw(),
                        ssid=traffic_rule.ssid.to_raw())

        return self.send_message(PT_DEL_TRAFFIC_RULE_QUEUE, msg)
