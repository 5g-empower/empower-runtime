#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
from empower.lvapp import PT_LVAP_LEAVE
from empower.lvapp import PT_CAPS_REQUEST
from empower.lvapp import CAPS_REQUEST
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
                LOG.info('Client inactive %s at %r',
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

        self._trigger_message(hdr.type)
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
            LOG.info("Hello from unknown WTP (%s)", (wtp_addr))
            return

        LOG.info("Hello from %s seq %u", self.addr[0], hello.seq)

        # compute delta if not new connection
        if wtp.connection:

            delta = time.time() - wtp.last_seen_ts

            # uplink
            ul_bytes = hello.uplink_bytes - wtp.uplink_bytes
            wtp.uplink_bytes_per_second = int(ul_bytes / delta) * 8

            # downlink
            dl_bytes = hello.downlink_bytes - wtp.downlink_bytes
            wtp.downlink_bytes_per_second = int(dl_bytes / delta) * 8

        # If this is a new connection, then send caps request
        if not wtp.connection:
            # set wtp before connection because it is used when the connection
            # attribute of the PNFDev object is set
            self.wtp = wtp
            wtp.connection = self
            self.send_caps_request()

        # Update WTP params
        wtp.period = hello.period
        wtp.last_seen = hello.seq
        wtp.uplink_bytes = hello.uplink_bytes
        wtp.downlink_bytes = hello.downlink_bytes

        wtp.last_seen_ts = time.time()

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
            LOG.info("Probe request from unknown WTP (%s)", (wtp_addr))
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

        if request.ssid == b'':
            LOG.info("Probe request from %s ssid %s", sta, "Broadcast")
        else:
            LOG.info("Probe request from %s ssid %s", sta,
                     SSID(request.ssid))

        # generate list of available SSIDs
        ssids = set()

        for tenant in RUNTIME.tenants.values():
            for wtp_in_tenant in tenant.wtps.values():
                if wtp_addr == wtp_in_tenant.addr:
                    ssids.add(SSID(tenant.tenant_name))

        if not ssids:
            LOG.info("No SSIDs available at this WTP")
            return

        # spawn new LVAP
        LOG.info("Spawning new LVAP %s on %s", sta, wtp.addr)
        bssid = self.server.generate_bssid(BASE_MAC, sta)
        lvap = LVAP(sta, bssid)
        lvap._ssids = ssids

        RUNTIME.lvaps[sta] = lvap

        # TODO: This should be built starting from the probe request
        lvap.supports.add(ResourceBlock(lvap, 1, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 2, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 3, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 4, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 5, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 6, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 7, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 8, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 9, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 10, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 11, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 36, BT_L20))
        lvap.supports.add(ResourceBlock(lvap, 48, BT_L20))

        # This will trigger an LVAP ADD message (and REMOVE if necessary)
        requested = ResourcePool()
        requested.add(ResourceBlock(wtp, request.channel, request.band))

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

        LOG.info("Auth request from %s, sending auth response", sta)
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

        matches = [x for x in RUNTIME.tenants.values()
                   if SSID(x.tenant_name) == ssid]

        if not matches:
            LOG.info("Assoc request to unknown SSID: %s ", request.ssid)
            return

        # this will trigger an add lvap message to update the ssid
        lvap.ssid = ssid

        # this will trigger an add lvap message to update the assoc id
        lvap.assoc_id = self.server.assoc_id

        LOG.info("Assoc request sta %s assoc id %u ssid %s, sending response",
                 lvap.addr,
                 lvap.assoc_id,
                 lvap.ssid)

        self.send_assoc_response(lvap)

    def _wait(self):
        """ Wait for incoming packets on signalling channel """
        self.__buffer = b''
        self.stream.read_bytes(4, self._on_read)

    def _on_disconnect(self):
        """ Handle WTP disconnection """

        if not self.wtp:
            return

        LOG.info("WTP disconnected: %s" % self.wtp.addr)

        # reset state
        self.wtp.last_seen = 0
        self.wtp.connection = None
        self.wtp.ports = {}
        self.wtp.supports = ResourcePool()

        # remove hosted LVAPs
        to_be_removed = []
        for lvap in RUNTIME.lvaps.values():
            if lvap.wtp == self.wtp:
                to_be_removed.append(lvap)

        for lvap in to_be_removed:
            LOG.info("LVAP LEAVE %s (%s)", lvap.addr, lvap.ssid)
            for handler in self.server.pt_types_handlers[PT_LVAP_LEAVE]:
                handler(lvap)
            LOG.info("Deleting LVAP: %s", lvap.addr)
            lvap.clear_ports()
            del RUNTIME.lvaps[lvap.addr]

        # remove hosted VAPs
        to_be_removed = []
        for vap in RUNTIME.vaps.values():
            if vap.wtp == self.wtp:
                to_be_removed.append(vap)

        for vap in to_be_removed:
            LOG.info("Deleting VAP: %s", vap.bssid)
            del RUNTIME.vaps[vap.bssid]

    def send_bye_message_to_self(self):
        """Send a unsollicited BYE message to senf."""

        for handler in self.server.pt_types_handlers[PT_BYE]:
            handler(self.wtp)

    def send_register_message_to_self(self):
        """Send a unsollicited BYE message to senf."""

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
            LOG.info("Status from unknown WTP %s", (wtp_addr))
            return

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", (wtp_addr))
            return

        sta_addr = EtherAddress(status.sta)
        set_mask = bool(status.flags.set_mask)

        lvap = None
        block = ResourceBlock(wtp, status.channel, status.band)

        LOG.info("LVAP %s status update block %s mask %s",
                 sta_addr,
                 block,
                 set_mask)

        # If the LVAP does not exists, then create a new one
        if sta_addr not in RUNTIME.lvaps:

            bssid_addr = EtherAddress(status.bssid)
            lvap = LVAP(sta_addr, bssid_addr)

            # TODO: This should be built starting from the status message
            lvap.supports.add(ResourceBlock(lvap, 1, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 2, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 3, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 4, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 5, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 6, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 7, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 8, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 9, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 10, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 11, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 36, BT_L20))
            lvap.supports.add(ResourceBlock(lvap, 48, BT_L20))

            RUNTIME.lvaps[sta_addr] = lvap

        lvap = RUNTIME.lvaps[sta_addr]

        # incoming block
        pool = ResourcePool()
        pool.add(block)

        match = wtp.supports & pool

        if not match:
            LOG.error("Incoming block is invalid")
            return

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
            LOG.error("Error while importing block %s, removing." % (block,))
            block.radio.connection.send_del_lvap(lvap)
            return

        lvap.authentication_state = bool(status.flags.authenticated)
        lvap.association_state = bool(status.flags.associated)

        lvap._assoc_id = status.assoc_id
        lvap._encap = EtherAddress(status.encap)
        ssids = [SSID(x.ssid) for x in status.ssids]

        if lvap.ssid:

            # Raise LVAP leave event
            LOG.info("LVAP LEAVE %s (%s)" % (lvap.addr, lvap.ssid))
            for handler in self.server.pt_types_handlers[PT_LVAP_LEAVE]:
                handler(lvap)

            # removing LVAP from tenant, need first to look for right tenant
            for tenant in RUNTIME.tenants.values():
                if lvap.ssid == SSID(tenant.tenant_name):
                    if lvap.addr in tenant.lvaps:
                        LOG.info("Removing %s from tenant %s" %
                                 (lvap.addr, tenant.tenant_name))
                        del tenant.lvaps[lvap.addr]
                        break

        lvap._ssid = None

        if ssids[0]:

            # setting ssid without seding out add lvap message
            lvap._ssid = ssids[0]

            # adding LVAP to tenant, need first to look for right tenant
            for tenant in RUNTIME.tenants.values():
                if lvap.ssid == SSID(tenant.tenant_name):
                    if lvap.addr not in tenant.lvaps:
                        LOG.info("Adding %s to tenant %s" %
                                 (lvap.addr, tenant.tenant_name))
                        tenant.lvaps[lvap.addr] = lvap

            # Raise LVAP join event
            LOG.info("LVAP JOIN %s (%s)" % (lvap.addr, lvap.ssid))
            for handler in self.server.pt_types_handlers[PT_LVAP_JOIN]:
                handler(lvap)

        # update remaining ssids
        lvap._ssids = [SSID(x) for x in ssids[1:]]

        # set ports
        lvap.set_ports()

        LOG.info("LVAP %s", lvap)

    def _handle_status_port(self, status):
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
            LOG.info("Status from unknown WTP %s", (wtp_addr))
            return

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", (wtp_addr))
            return

        sta_addr = EtherAddress(status.sta)

        LOG.info("Port status update for %s from %s channel %u band %s",
                 sta_addr,
                 wtp_addr,
                 status.channel,
                 status.band)

        block = ResourceBlock(wtp, status.channel, status.band)

        try:
            lvap = RUNTIME.lvaps[sta_addr]
        except KeyError:
            LOG.error("Invalid LVAP %s, ignoring" % sta_addr)
            return

        try:
            port = lvap.downlink[block]
        except KeyError:
            LOG.error("Invalid Block %s, ignoring" % block)
            return

        port._no_ack = bool(status.flags.no_ack)
        port._rts_cts = int(status.rts_cts)
        port._mcs = set(status.mcs)
        port._tx_power = int(status.tx_power)

        LOG.info("Port: %s", port)

    def _handle_caps_response(self, caps):
        """Handle an incoming CAPS_RESPONSE message.
        Args:
            caps, a CAPS_RESPONSE message
        Returns:
            None
        """

        wtp_addr = EtherAddress(caps.wtp)

        try:
            wtp = RUNTIME.wtps[wtp_addr]
        except KeyError:
            LOG.info("Caps response from unknown WTP (%s)", (wtp_addr))
            return

        LOG.info("Received caps response from %s",
                 EtherAddress(caps.wtp))

        for block in caps.blocks:

            r_block = ResourceBlock(wtp, block[0], block[1])
            wtp.supports.add(r_block)

        for port in caps.ports:

            iface = port[2].decode("utf-8").strip('\0')

            network_port = NetworkPort(dpid=wtp.addr,
                                       hwaddr=EtherAddress(port[0]),
                                       port_id=int(port[1]),
                                       iface=iface)

            wtp.ports[network_port.port_id] = network_port

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

            tokens = [tenant_id.hex[0:12][i:i+2] for i in range(0, 12, 2)]

            base_bssid = EtherAddress(':'.join(tokens))

            for block in wtp.supports:

                net_bssid = self.server.generate_bssid(base_bssid, wtp_addr)

                # vap has already been created
                if net_bssid in RUNTIME.vaps:
                    continue

                vap = VAP(net_bssid, tenant.tenant_name, block)

                self.send_add_vap(vap)
                RUNTIME.tenants[tenant_id].vaps[net_bssid] = vap
                break

    def _handle_interference_map(self, interference_map):
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
            LOG.info("Status from unknown WTP %s", (wtp_addr))
            return

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", (wtp_addr))
            return

        LOG.info("Received interference map from %s", wtp.addr)

        for block in wtp.supports:
            block.rssi_to = {}

        for block in wtp.supports:
            for entry in interference_map.map_entries:
                sta = EtherAddress(entry[0])
                if sta in RUNTIME.lvaps or sta in RUNTIME.wtps:
                    block.rssi_to[sta] = entry[1]

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
                            length=16,
                            seq=self.wtp.seq,
                            channel=vap.channel,
                            band=vap.band,
                            net_bssid=vap.net_bssid.to_raw(),
                            ssid=vap.tenant_ssid.encode())

        add_vap.length = add_vap.length + len(vap.tenant_ssid)
        LOG.info("Add vap bssid %s band %s channel %d ssid %s",
                 vap.net_bssid, vap.band, vap.channel, vap.tenant_ssid)

        msg = ADD_VAP.build(add_vap)
        self.stream.write(msg)

    def send_caps_request(self):
        """Send a CAPS_REQUEST message.
        Args:
            None
        Returns:
            None
        Raises:
            TypeError: if sta is not an EtherAddress object.
        """

        caps_req = Container(version=PT_VERSION,
                             type=PT_CAPS_REQUEST,
                             length=10,
                             seq=self.wtp.seq)

        LOG.info("Sending caps request to %s", self.wtp.addr)

        msg = CAPS_REQUEST.build(caps_req)
        self.stream.write(msg)

    def _handle_status_vap(self, status):
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
            LOG.info("VAP Status from unknown WTP %s", (wtp_addr))
            return

        if not wtp.connection:
            LOG.info("VAP Status from disconnected WTP %s", (wtp_addr))
            return

        bssid_addr = EtherAddress(status.bssid)

        vap = None
        block = ResourceBlock(wtp, status.channel, status.band)
        ssid = status.ssid

        LOG.info("VAP %s status update block %s",
                 bssid_addr,
                 block)

        # If the VAP does not exists, then create a new one
        if bssid_addr not in RUNTIME.vaps:
            RUNTIME.vaps[bssid_addr] = VAP(bssid_addr, ssid, block)

        vap = RUNTIME.vaps[bssid_addr]
        LOG.info("VAP %s", vap)

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
                             length=14,
                             seq=self.wtp.seq,
                             sta=lvap.addr.to_raw())

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

        LOG.info("Del lvap %s from wtp %s" % (lvap.addr, self.wtp.addr))
        msg = DEL_LVAP.build(del_lvap)
        self.stream.write(msg)

    def send_set_port(self, port):
        """Send a SET_PORT message.
        Args:
            port: a Port object
        Returns:
            None
        Raises:
            TypeError: if lvap is not an LVAP object.
        """

        flags = Container(no_ack=port.no_ack)

        set_port = Container(version=PT_VERSION,
                             type=PT_SET_PORT,
                             length=20 + len(port.mcs),
                             seq=self.wtp.seq,
                             flags=flags,
                             sta=port.lvap.addr.to_raw(),
                             tx_power=port.tx_power,
                             rts_cts=port.rts_cts,
                             nb_mcses=len(port.mcs),
                             mcs=sorted(list(port.mcs)))

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

        add_lvap = Container(version=PT_VERSION,
                             type=PT_ADD_LVAP,
                             length=32,
                             seq=self.wtp.seq,
                             flags=flags,
                             assoc_id=lvap.assoc_id,
                             channel=block.channel,
                             band=block.band,
                             sta=lvap.addr.to_raw(),
                             encap=lvap.encap.to_raw(),
                             bssid=lvap.bssid.to_raw(),
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

        LOG.info("Add lvap %s block %s mask %s" % (lvap.addr, block, set_mask))

        msg = ADD_LVAP.build(add_lvap)
        self.stream.write(msg)
