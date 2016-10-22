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

import tornado.ioloop
import time

from construct import Container

from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.ssid import SSID
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.core.resourcepool import BT_L20
from empower.core.radioport import RadioPort
from empower.lvapp import HEADER
from empower.lvapp import PT_VERSION
from empower.lvapp import PT_BYE
from empower.lvapp import PT_REGISTER
from empower.lvapp import PT_LVAP_JOIN
from empower.lvapp import PT_AUTH_RESPONSE
from empower.lvapp import AUTH_RESPONSE
from empower.lvapp import PT_ASSOC_RESPONSE
from empower.lvapp import ASSOC_RESPONSE
from empower.lvapp import PT_SET_PORT
from empower.lvapp import SET_PORT
from empower.lvapp import PT_ADD_LVAP
from empower.lvapp import ADD_LVAP
from empower.lvapp import PT_DEL_LVAP
from empower.lvapp import DEL_LVAP
from empower.lvapp import PT_PROBE_RESPONSE
from empower.lvapp import PROBE_RESPONSE
from empower.core.lvap import LVAP
from empower.core.networkport import NetworkPort
from empower.core.vap import VAP
from empower.lvapp import PT_ADD_VAP
from empower.lvapp import ADD_VAP
from empower.core.tenant import T_TYPE_SHARED
from empower.core.tenant import T_TYPE_UNIQUE
from empower.core.utils import generate_bssid

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

BASE_MAC = EtherAddress("00:1b:b3:00:00:00")


class LVAPPConnection(object):
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

    def to_dict(self):
        """Return dict representation of object."""

        return self.addr

    def _heartbeat_cb(self):
        """ Check if wtp connection is still active. Disconnect if no hellos
        have been received from the wtp for twice the hello period. """
        if self.wtp and not self.stream.closed():
            timeout = (self.wtp.period / 1000) * 3
            if (self.wtp.last_seen_ts + timeout) < time.time():
                LOG.info('Client inactive %s at %r', self.wtp.addr, self.addr)
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
            LOG.exception(ex)
            self.stream.close()
            return

        self._wait()

    def _trigger_message(self, msg_type):

        if msg_type not in self.server.pt_types:

            LOG.error("Unknown message type %u", msg_type)
            return

        if self.server.pt_types[msg_type]:

            msg = self.server.pt_types[msg_type].parse(self.__buffer)
            handler_name = "_handle_%s" % self.server.pt_types[msg_type].name

            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                handler(msg)

        if msg_type in self.server.pt_types_handlers:
            for handler in self.server.pt_types_handlers[msg_type]:
                handler(msg)

    def _handle_hello(self, hello):
        """Handle an incoming HELLO message.
        Args:
            hello, a HELLO message
        Returns:
            None
        """

        wtp_addr = EtherAddress(hello.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Hello from unknown WTP (%s)", wtp_addr)
            return

        LOG.info("Hello from %s WTP %s seq %u", self.addr[0], wtp.addr,
                 hello.seq)

        # New connection
        if not wtp.connection:

            # set pointer to pnfdev object
            self.wtp = wtp

            # set connection
            wtp.connection = self

        # Update WTP params
        wtp.period = hello.period
        wtp.last_seen = hello.seq
        wtp.last_seen_ts = time.time()

        # Upon connection to the controller, the WTP must be provided
        # with the list of shared VAP
        for tenant in RUNTIME.tenants.values():

            # tenant does not use shared VAPs
            if tenant.bssid_type == T_TYPE_UNIQUE:
                continue

            # wtp not in this tenant
            if wtp_addr not in tenant.wtps:
                continue

            tenant_id = tenant.tenant_id
            tokens = [tenant_id.hex[0:12][i:i + 2] for i in range(0, 12, 2)]
            base_bssid = EtherAddress(':'.join(tokens))

            for block in wtp.supports:

                net_bssid = generate_bssid(base_bssid, block.hwaddr)

                # vap has already been created
                if net_bssid in RUNTIME.tenants[tenant_id].vaps:
                    continue

                vap = VAP(net_bssid, block, wtp, tenant)

                self.send_add_vap(vap)
                RUNTIME.tenants[tenant_id].vaps[net_bssid] = vap

    def _handle_probe_request(self, request):
        """Handle an incoming PROBE_REQUEST message.
        Args:
            request, a PROBE_REQUEST message
        Returns:
            None
        """

        wtp_addr = EtherAddress(request.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Probe request from unknown WTP (%s)", wtp_addr)
            return

        if not wtp.connection:
            LOG.info("Probe request from disconnected WTP %s", wtp_addr)
            return

        sta = EtherAddress(request.sta)

        if sta in RUNTIME.lvaps:
            return

        if not RUNTIME.is_allowed(sta):
            return

        if RUNTIME.is_denied(sta):
            return

        ssid = SSID(request.ssid)

        if request.ssid == b'':
            LOG.info("Probe request from %s ssid %s", sta, "Broadcast")
        else:
            LOG.info("Probe request from %s ssid %s", sta, ssid)

        # generate list of available SSIDs
        ssids = set()

        for tenant in RUNTIME.tenants.values():
            if tenant.bssid_type == T_TYPE_SHARED:
                continue
            for wtp_in_tenant in tenant.wtps.values():
                if wtp_addr == wtp_in_tenant.addr:
                    ssids.add(tenant.tenant_name)

        if not ssids:
            LOG.info("No SSIDs available at this WTP")
            return

        # spawn new LVAP
        LOG.info("Spawning new LVAP %s on %s", sta, wtp.addr)
        net_bssid = generate_bssid(BASE_MAC, sta)
        lvap = LVAP(sta, net_bssid, net_bssid)
        lvap.set_ssids(list(ssids))

        RUNTIME.lvaps[sta] = lvap

        # TODO: This should be built starting from the probe request
        lvap.supports.add(ResourceBlock(lvap, sta, 1, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 2, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 3, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 4, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 5, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 6, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 7, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 8, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 9, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 10, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 11, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 36, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, sta, 48, BT_L20))

        # This will trigger an LVAP ADD message (and REMOVE if necessary)
        requested = ResourcePool()
        hwaddr = EtherAddress(request.hwaddr)
        channel = request.channel
        band = request.band
        requested.add(ResourceBlock(wtp, hwaddr, channel, band))

        lvap.scheduled_on = wtp.supports & requested

        LOG.info("Sending probe response to %s", lvap.addr)
        self.send_probe_response(lvap)

    def _handle_auth_request(self, request):
        """Handle an incoming AUTH_REQUEST message.
        Args:
            request, a AUTH_REQUEST message
        Returns:
            None
        """

        wtp_addr = EtherAddress(request.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Auth request from unknown WTP %s", wtp_addr)
            return

        if not wtp.connection:
            LOG.info("Auth request from disconnected WTP %s", wtp_addr)
            return

        sta = EtherAddress(request.sta)
        bssid = EtherAddress(request.bssid)

        if sta not in RUNTIME.lvaps:
            LOG.info("Auth request from unknown LVAP %s", sta)
            return

        lvap = RUNTIME.lvaps[sta]

        if not RUNTIME.is_allowed(sta):
            LOG.info("Auth request from %s ignored (white list)", sta)
            return

        if RUNTIME.is_denied(sta):
            LOG.info("Auth request from %s ignored (black list)", sta)
            return

        lvap_bssid = None

        # the request bssid is the lvap's unique bssid
        if lvap.net_bssid == bssid:

            lvap_bssid = lvap.net_bssid

        # else if is a shared bssid
        else:

            shared_tenants = [x for x in RUNTIME.tenants.values()
                              if x.bssid_type == T_TYPE_SHARED]

            wtp = RUNTIME.wtps[wtp_addr]

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

        LOG.info("Auth request from %s for BSSID %s, replying", sta, bssid)

        self.send_auth_response(lvap)

    def _handle_assoc_request(self, request):
        """Handle an incoming ASSOC_REQUEST message.
        Args:
            request, a ASSOC_REQUEST message
        Returns:
            None
        """

        wtp_addr = EtherAddress(request.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Assoc request from unknown WTP %s", wtp_addr)
            return

        if not wtp.connection:
            LOG.info("Assoc request from disconnected WTP %s", wtp_addr)
            return

        sta = EtherAddress(request.sta)

        if sta not in RUNTIME.lvaps:
            LOG.info("Assoc request from unknown LVAP %s", sta)
            return

        lvap = RUNTIME.lvaps[sta]

        if not RUNTIME.is_allowed(sta):
            LOG.info("Assoc request from %s ignored (white list)", sta)
            return

        if RUNTIME.is_denied(sta):
            LOG.info("Assoc request from %s ignored (black list)", sta)
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
            LOG.info("Assoc request sta %s for ssid %s bssid %s, ignoring",
                     lvap.addr, lvap.ssid, lvap.lvap_bssid)
            return

        # this will trigger an add lvap message to update the ssid
        lvap.tenant = RUNTIME.load_tenant(tenant_name)

        # this will trigger an add lvap message to update the assoc id
        lvap.assoc_id = self.server.assoc_id

        LOG.info("Assoc request sta %s ssid %s bssid %s assoc id %u, replying",
                 lvap.addr, lvap.ssid, lvap.lvap_bssid, lvap.assoc_id)

        self.send_assoc_response(lvap)

    def _wait(self):
        """ Wait for incoming packets on signalling channel """
        self.__buffer = b''
        self.stream.read_bytes(4, self._on_read)

    def _on_disconnect(self):
        """ Handle WTP disconnection """

        if not self.wtp:
            return

        LOG.info("WTP disconnected: %s", self.wtp.addr)

        # remove hosted lvaps
        for addr in list(RUNTIME.lvaps.keys()):
            lvap = RUNTIME.lvaps[addr]
            # in case the downlink went down, the remove also the uplinks
            if lvap.wtp == self.wtp:
                LOG.info("Deleting LVAP (DL+UL): %s", lvap.addr)
                lvap.clear_downlink()
                lvap.clear_uplink()
                self.server.send_lvap_leave_message_to_self(lvap)
                del RUNTIME.lvaps[lvap.addr]
            else:
                LOG.info("Deleting LVAP (UL): %s", lvap.addr)
                lvap.clear_uplink()

        # remove hosted vaps
        for tenant_id in RUNTIME.tenants.keys():
            for vap_id in list(RUNTIME.tenants[tenant_id].vaps.keys()):
                vap = RUNTIME.tenants[tenant_id].vaps[vap_id]
                if vap.wtp == self.wtp:
                    LOG.info("Deleting VAP: %s", vap.net_bssid)
                    del RUNTIME.tenants[vap.tenant_id].vaps[vap.net_bssid]

        # reset state
        self.wtp.last_seen = 0
        self.wtp.connection = None
        self.wtp.ports = {}
        self.wtp.supports = ResourcePool()

    def send_bye_message_to_self(self):
        """Send a unsollicited BYE message to senf."""

        for handler in self.server.pt_types_handlers[PT_BYE]:
            handler(self.wtp)

    def send_register_message_to_self(self):
        """Send a unsollicited REGISTER message to senf."""

        for handler in self.server.pt_types_handlers[PT_REGISTER]:
            handler(self.wtp)

    def _handle_status_lvap(self, status):
        """Handle an incoming STATUS_LVAP message.
        Args:
            status, a STATUS_LVAP message
        Returns:
            None
        """

        wtp_addr = EtherAddress(status.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Status from unknown WTP %s", wtp_addr)
            return

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", wtp_addr)
            return

        sta_addr = EtherAddress(status.sta)
        set_mask = bool(status.flags.set_mask)

        lvap = None
        hwaddr = EtherAddress(status.hwaddr)
        block = ResourceBlock(wtp, hwaddr, status.channel, status.band)

        LOG.info("LVAP status update from %s", sta_addr)

        # If the LVAP does not exists, then create a new one
        if sta_addr not in RUNTIME.lvaps:

            net_bssid_addr = EtherAddress(status.net_bssid)
            lvap_bssid_addr = EtherAddress(status.lvap_bssid)
            lvap = LVAP(sta_addr, net_bssid_addr, lvap_bssid_addr)

            # TODO: This should be built starting from the status message
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 1, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 2, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 3, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 4, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 5, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 6, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 7, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 8, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 9, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 10, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 11, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 36, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, sta_addr, 48, BT_L20))

            RUNTIME.lvaps[sta_addr] = lvap

        lvap = RUNTIME.lvaps[sta_addr]

        # incoming block
        pool = ResourcePool()
        pool.add(block)

        match = wtp.supports & pool

        if not match:
            LOG.error("Incoming block %s is invalid", block)
            return

        block = match.pop()

        # this will try to updated the lvap object with the resource block
        # coming in this status update message.
        try:

            if set_mask:

                # set downlink+uplink block
                lvap._downlink.setitem(block, RadioPort(lvap, block))

            else:

                # set uplink only blocks
                lvap._uplink.setitem(block, RadioPort(lvap, block))

        except ValueError:
            LOG.error("Error while importing block %s, removing.", block)
            block.radio.connection.send_del_lvap(lvap)
            return

        lvap.authentication_state = bool(status.flags.authenticated)
        lvap.association_state = bool(status.flags.associated)

        lvap._assoc_id = status.assoc_id
        lvap._encap = EtherAddress(status.encap)
        ssids = [SSID(x.ssid) for x in status.ssids]

        if lvap.ssid:

            # Raise LVAP leave event
            self.server.send_lvap_leave_message_to_self(lvap)

            # removing LVAP from tenant, need first to look for right tenant
            if lvap.addr in lvap.tenant.lvaps:
                LOG.info("Removing %s from tenant %s", lvap.addr, lvap.ssid)
                del lvap.tenant.lvaps[lvap.addr]

        lvap._tenant = None

        if ssids[0]:

            # setting tenant without seding out add lvap message
            lvap._tenant = RUNTIME.load_tenant(ssids[0])

            # adding LVAP to tenant
            LOG.info("Adding %s to tenant %s", lvap.addr, ssids[0])
            lvap.tenant.lvaps[lvap.addr] = lvap

            # Raise LVAP join event
            LOG.info("LVAP JOIN %s (%s)", lvap.addr, lvap.ssid)
            for handler in self.server.pt_types_handlers[PT_LVAP_JOIN]:
                handler(lvap)

        # update remaining ssids
        lvap._ssids = ssids[1:]

        # set ports
        lvap.set_ports()

        LOG.info("LVAP status %s", lvap)

    @classmethod
    def _handle_status_port(cls, status):
        """Handle an incoming PORT message.
        Args:
            status, a STATUS_PORT message
        Returns:
            None
        """

        wtp_addr = EtherAddress(status.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Status from unknown WTP %s", wtp_addr)
            return

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", wtp_addr)
            return

        sta_addr = EtherAddress(status.sta)
        hwaddr = EtherAddress(status.hwaddr)
        block = ResourceBlock(wtp, hwaddr, status.channel, status.band)

        # incoming block
        pool = ResourcePool()
        pool.add(block)

        match = wtp.supports & pool

        if not match:
            LOG.error("Incoming block %s is invalid", block)
            return

        block = match.pop()

        LOG.info("Port status from %s, station %s", wtp_addr, sta_addr)

        tx_policy = block.tx_policies[sta_addr]

        tx_policy._mcs = set([float(x) / 2 for x in status.mcs])
        tx_policy._rts_cts = int(status.rts_cts)
        tx_policy._mcast = int(status.tx_mcast)
        tx_policy._ur_count = int(status.ur_mcast_count)
        tx_policy._no_ack = bool(status.flags.no_ack)

        LOG.info("Port status %s", tx_policy)

    def _handle_caps(self, caps):
        """Handle an incoming CAPS message.
        Args:
            caps, a CAPS message
        Returns:
            None
        """

        wtp_addr = EtherAddress(caps.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Caps response from unknown WTP (%s)", wtp_addr)
            return

        LOG.info("Received caps from %s", wtp_addr)

        for block in caps.blocks:

            hwaddr = EtherAddress(block[0])

            r_block = ResourceBlock(wtp, hwaddr, block[1], block[2])
            wtp.supports.add(r_block)

        for port in caps.ports:

            iface = port[2].decode("utf-8").strip('\0')

            network_port = NetworkPort(dpid=wtp.addr,
                                       hwaddr=EtherAddress(port[0]),
                                       port_id=int(port[1]),
                                       iface=iface)

            wtp.ports[network_port.port_id] = network_port

        # WTP can be considered as available once the empower0 port has been
        # added to the OVS
        if wtp.port():
            self.send_register_message_to_self()

    @classmethod
    def _handle_interference_map(cls, interference_map):
        """Handle an incoming INTERFERENCE_MAP message.
        Args:
            interference_map, an INTERFERENCE_MAP message
        Returns:
            None
        """

        wtp_addr = EtherAddress(interference_map.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Status from unknown WTP %s", wtp_addr)
            return

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", wtp_addr)
            return

        LOG.info("Received interference map from %s", wtp.addr)

        for block in wtp.supports:
            block.rssi_to = {}

        for block in wtp.supports:
            for entry in interference_map.map_entries:
                sta = EtherAddress(entry[0])
                if sta in RUNTIME.lvaps or sta in RUNTIME.wtps:
                    block.rssi_to[sta] = entry[1]

    @classmethod
    def _handle_status_vap(cls, status):
        """Handle an incoming STATUS_VAP message.
        Args:
            status, a STATUS_VAP message
        Returns:
            None
        """

        wtp_addr = EtherAddress(status.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("VAP Status from unknown WTP %s", wtp_addr)
            return

        if not wtp.connection:
            LOG.info("VAP Status from disconnected WTP %s", wtp_addr)
            return

        net_bssid_addr = EtherAddress(status.net_bssid)
        ssid = SSID(status.ssid)
        tenant_id = None

        for tenant in RUNTIME.tenants.values():
            if tenant.tenant_name == ssid:
                tenant_id = tenant.tenant_id
                break

        if not tenant_id:
            LOG.info("VAP %s from unknown tenant %s", net_bssid_addr, ssid)
            return

        tenant = RUNTIME.tenants[tenant_id]

        vap = None
        hwaddr = EtherAddress(status.hwaddr)
        block = ResourceBlock(wtp, hwaddr, status.channel, status.band)
        ssid = status.ssid

        LOG.info("VAP %s status update block %s", net_bssid_addr, block)

        # If the VAP does not exists, then create a new one
        if net_bssid_addr not in tenant.vaps:
            tenant.vaps[net_bssid_addr] = \
                VAP(net_bssid_addr, block, wtp, tenant)

        vap = tenant.vaps[net_bssid_addr]
        LOG.info("VAP status %s", vap)

    def send_add_vap(self, vap):
        """Send a ADD_VAP message.
        Args:
            vap: an VAP object
        Returns:
            None
        Raises:
            TypeError: if vap is not an VAP object
        """

        add_vap = Container(version=PT_VERSION,
                            type=PT_ADD_VAP,
                            length=22,
                            seq=self.wtp.seq,
                            hwaddr=vap.block.hwaddr.to_raw(),
                            channel=vap.block.channel,
                            band=vap.block.band,
                            net_bssid=vap.net_bssid.to_raw(),
                            ssid=vap.ssid.to_raw())

        add_vap.length = add_vap.length + len(vap.ssid)
        LOG.info("Add vap %s", vap)

        msg = ADD_VAP.build(add_vap)
        self.stream.write(msg)

    def send_assoc_response(self, lvap):
        """Send a ASSOC_RESPONSE message.
        Args:
            lvap: an LVAP object
        Returns:
            None
        Raises:
            TypeError: if lvap is not an LVAP object.
        """

        response = Container(version=PT_VERSION,
                             type=PT_ASSOC_RESPONSE,
                             length=14,
                             seq=self.wtp.seq,
                             sta=lvap.addr.to_raw())

        msg = ASSOC_RESPONSE.build(response)
        self.stream.write(msg)

    def send_auth_response(self, lvap):
        """Send a AUTH_RESPONSE message.
        Args:
            lvap: an LVAP object
        Returns:
            None
        Raises:
            TypeError: if lvap is not an LVAP object.
        """

        response = Container(version=PT_VERSION,
                             type=PT_AUTH_RESPONSE,
                             length=20,
                             seq=self.wtp.seq,
                             sta=lvap.addr.to_raw(),
                             bssid=lvap.lvap_bssid.to_raw())

        msg = AUTH_RESPONSE.build(response)
        self.stream.write(msg)

    def send_probe_response(self, lvap):
        """Send a PROBE_RESPONSE message.
        Args:
            lvap: an LVAP object
        Returns:
            None
        Raises:
            TypeError: if lvap is not an LVAP object.
        """

        response = Container(version=PT_VERSION,
                             type=PT_PROBE_RESPONSE,
                             length=14,
                             seq=self.wtp.seq,
                             sta=lvap.addr.to_raw())

        msg = PROBE_RESPONSE.build(response)
        self.stream.write(msg)

    def send_del_lvap(self, lvap):
        """Send a DEL_LVAP message.
        Args:
            lvap: an LVAP object
        Returns:
            None
        Raises:
            TypeError: if lvap is not an LVAP object.
        """

        del_lvap = Container(version=PT_VERSION,
                             type=PT_DEL_LVAP,
                             length=14,
                             seq=self.wtp.seq,
                             sta=lvap.addr.to_raw())

        msg = DEL_LVAP.build(del_lvap)
        self.stream.write(msg)

    def send_set_port(self, tx_policy):
        """Send a SET_PORT message.
        Args:
            port: a Port object
        Returns:
            None
        Raises:
            TypeError: if lvap is not an LVAP object.
        """

        flags = Container(no_ack=tx_policy.no_ack)
        rates = sorted([int(x * 2) for x in tx_policy.mcs])

        set_port = Container(version=PT_VERSION,
                             type=PT_SET_PORT,
                             length=29 + len(rates),
                             seq=self.wtp.seq,
                             flags=flags,
                             sta=tx_policy.addr.to_raw(),
                             hwaddr=tx_policy.block.hwaddr.to_raw(),
                             channel=tx_policy.block.channel,
                             band=tx_policy.block.band,
                             rts_cts=tx_policy.rts_cts,
                             tx_mcast=tx_policy.mcast,
                             ur_mcast_count=tx_policy.ur_count,
                             nb_mcses=len(rates),
                             mcs=rates)

        LOG.info("Set tx policy %s", tx_policy)

        msg = SET_PORT.build(set_port)
        self.stream.write(msg)

    def send_add_lvap(self, lvap, block, set_mask):
        """Send a ADD_LVAP message.
        Args:
            lvap: an LVAP object
        Returns:
            None
        Raises:
            TypeError: if lvap is not an LVAP object.
        """

        flags = Container(authenticated=lvap.authentication_state,
                          associated=lvap.association_state,
                          set_mask=set_mask)

        encap = EtherAddress("00:00:00:00:00:00")

        if lvap.encap:
            encap = lvap.encap

        add_lvap = Container(version=PT_VERSION,
                             type=PT_ADD_LVAP,
                             length=44,
                             seq=self.wtp.seq,
                             flags=flags,
                             assoc_id=lvap.assoc_id,
                             hwaddr=block.hwaddr.to_raw(),
                             channel=block.channel,
                             band=block.band,
                             sta=lvap.addr.to_raw(),
                             encap=encap.to_raw(),
                             net_bssid=lvap.net_bssid.to_raw(),
                             lvap_bssid=lvap.lvap_bssid.to_raw(),
                             ssids=[])

        if lvap.ssid:
            b_ssid = lvap.ssid.to_raw()
            tmp = Container(length=len(b_ssid), ssid=b_ssid)
            add_lvap.ssids.append(tmp)
            add_lvap.length = add_lvap.length + len(b_ssid) + 1
        else:
            add_lvap.ssids.append(Container(length=0, ssid=b''))
            add_lvap.length = add_lvap.length + 1

        for ssid in lvap.ssids:
            b_ssid = ssid.to_raw()
            tmp = Container(length=len(b_ssid), ssid=b_ssid)
            add_lvap.ssids.append(tmp)
            add_lvap.length = add_lvap.length + len(b_ssid) + 1

        LOG.info("Add lvap %s", lvap)

        msg = ADD_LVAP.build(add_lvap)
        self.stream.write(msg)
