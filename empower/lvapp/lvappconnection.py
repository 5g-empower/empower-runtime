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

from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.ssid import SSID
from empower.core.resourcepool import ResourceBlock
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
from empower.lvapp import PT_ADD_LVAP_RESPONSE
from empower.lvapp import PT_DEL_LVAP_RESPONSE
from empower.core.lvap import LVAP
from empower.core.networkport import NetworkPort
from empower.core.vap import VAP
from empower.lvapp import PT_ADD_VAP
from empower.lvapp import ADD_VAP
from empower.core.tenant import T_TYPE_SHARED
from empower.core.tenant import T_TYPE_UNIQUE
from empower.core.utils import generate_bssid
from empower.core.virtualport import VirtualPortLvap

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

BASE_MAC = EtherAddress("02:ca:fe:00:00:00")


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

        if not self.stream.closed():
            self._wait()

    def _trigger_message(self, msg_type):

        if msg_type not in self.server.pt_types:
            LOG.error("Unknown message type %u", msg_type)
            return

        if self.server.pt_types[msg_type]:

            LOG.info("Got message type %u (%s)", msg_type,
                     self.server.pt_types[msg_type].name)

            msg = self.server.pt_types[msg_type].parse(self.__buffer)
            addr = EtherAddress(msg.wtp)

            try:
                wtp = RUNTIME.wtps[addr]
            except KeyError:
                LOG.error("Unknown WTP (%s), closing connection", addr)
                self.stream.close()
                return

            handler_name = "_handle_%s" % self.server.pt_types[msg_type].name

            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                handler(wtp, msg)

            if msg_type in self.server.pt_types_handlers:
                for handler in self.server.pt_types_handlers[msg_type]:
                    handler(msg)

    def _handle_add_del_lvap(self, wtp, status):
        """Handle an incoming ADD_DEL_LVAP message.
        Args:
            status, a ADD_DEL_LVAP message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("Add/del response from disconnected WTP %s", wtp.addr)
            return

        if status.type == PT_ADD_LVAP_RESPONSE:
            msg_subtype = "add_lvap"
        else:
            msg_subtype = "del_lvap"

        LOG.info("%s from %s WTP %s module_id %u status %u", msg_subtype,
                 EtherAddress(status.sta), EtherAddress(status.wtp),
                 status.module_id, status.status)

        sta = EtherAddress(status.sta)

        if sta not in RUNTIME.lvaps:
            LOG.info("Add/del response from unknown LVAP %s", sta)
            return

        lvap = RUNTIME.lvaps[sta]

        if status.module_id in lvap.pending:
            LOG.info("LVAP %s, pending module id %s found. Removing.",
                     lvap.addr, status.module_id)
            idx = lvap.pending.index(status.module_id)
            del lvap.pending[idx]
        else:
            LOG.info("LVAP %s, pending module id %s not found. Ignoring.",
                     lvap.addr, status.module_id)

    def _handle_hello(self, wtp, hello):
        """Handle an incoming HELLO message.
        Args:
            hello, a HELLO message
        Returns:
            None
        """

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
            if wtp.addr not in tenant.wtps:
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

    def _handle_probe_request(self, wtp, request):
        """Handle an incoming PROBE_REQUEST message.
        Args:
            request, a PROBE_REQUEST message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("Probe request from disconnected WTP %s", wtp.addr)
            self.stream.close()
            return

        if not wtp.port():
            LOG.info("WTP %s not ready", wtp.addr)
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
                if wtp.addr == wtp_in_tenant.addr:
                    ssids.add(tenant.tenant_name)

        if not ssids:
            LOG.info("No SSIDs available at this WTP")
            return

        # spawn new LVAP
        LOG.info("Spawning new LVAP %s on %s", sta, wtp.addr)
        net_bssid = generate_bssid(BASE_MAC, sta)
        lvap = LVAP(sta, net_bssid, net_bssid)
        lvap.set_ssids(list(ssids))

        # set supported band
        lvap.supported_band = request.supported_band

        # Check if block is valid
        incoming = ResourceBlock(wtp, EtherAddress(request.hwaddr),
                                 request.channel, request.band)

        valid = [block for block in wtp.supports if block == incoming]

        if not valid:
            LOG.warning("No valid intersection found. Ignoring request.")
            return

        # This will trigger an LVAP ADD message (and REMOVE if necessary)
        lvap.blocks = valid[0]

        # save LVAP in the runtime
        RUNTIME.lvaps[sta] = lvap

        LOG.info("Sending probe response to %s", lvap.addr)
        self.send_probe_response(lvap, ssid)

    def _handle_auth_request(self, wtp, request):
        """Handle an incoming AUTH_REQUEST message.
        Args:
            request, a AUTH_REQUEST message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("Auth request from disconnected WTP %s", wtp.addr)
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

        LOG.info("Auth request from %s for BSSID %s, replying", sta, bssid)

        self.send_auth_response(lvap)

    def _handle_assoc_request(self, wtp, request):
        """Handle an incoming ASSOC_REQUEST message.
        Args:
            request, a ASSOC_REQUEST message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("Assoc request from disconnected WTP %s", wtp.addr)
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

        # set supported band
        lvap.supported_band = request.supported_band

        # this will trigger an add lvap message to update the assoc id
        lvap.assoc_id = self.server.assoc_id

        LOG.info("Assoc request sta %s ssid %s bssid %s assoc id %u, replying",
                 lvap.addr, lvap.ssid, lvap.lvap_bssid, lvap.assoc_id)

        self.send_assoc_response(lvap)

    def _wait(self):
        """ Wait for incoming packets on signalling channel """
        self.__buffer = b''
        self.stream.read_bytes(6, self._on_read)

    def _on_disconnect(self):
        """ Handle WTP disconnection """

        if not self.wtp:
            return

        LOG.info("WTP disconnected: %s", self.wtp.addr)

        # remove hosted lvaps
        for addr in list(RUNTIME.lvaps.keys()):
            lvap = RUNTIME.lvaps[addr]
            dl_wtps = [block.radio for block in lvap.downlink.keys()]
            ul_wtps = [block.radio for block in lvap.uplink.keys()]
            # in case the downlink went down, the remove also the uplinks
            if self.wtp in dl_wtps:
                RUNTIME.remove_lvap(lvap.addr)
            elif self.wtp in ul_wtps:
                LOG.info("Deleting LVAP (UL): %s", lvap.addr)
                lvap.clear_uplink()

        # remove hosted vaps
        for tenant_id in RUNTIME.tenants.keys():
            for vap_id in list(RUNTIME.tenants[tenant_id].vaps.keys()):
                vap = RUNTIME.tenants[tenant_id].vaps[vap_id]
                if vap.wtp == self.wtp:
                    LOG.info("Deleting VAP: %s", vap.net_bssid)
                    del RUNTIME.tenants[tenant_id].vaps[vap.net_bssid]

        # reset state
        self.wtp.last_seen = 0
        self.wtp.connection = None
        self.wtp.ports = {}
        self.wtp.supports = set()
        self.wtp = None

    def send_bye_message_to_self(self):
        """Send a unsollicited BYE message to senf."""

        for handler in self.server.pt_types_handlers[PT_BYE]:
            handler(self.wtp)

    def send_register_message_to_self(self):
        """Send a unsollicited REGISTER message to senf."""

        for handler in self.server.pt_types_handlers[PT_REGISTER]:
            handler(self.wtp)

    def _handle_status_lvap(self, wtp, status):
        """Handle an incoming STATUS_LVAP message.
        Args:
            status, a STATUS_LVAP message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", wtp.addr)
            return

        sta = EtherAddress(status.sta)
        set_mask = bool(status.flags.set_mask)

        lvap = None

        accum = []
        incoming_ssids = [SSID(x.ssid) for x in status.ssids]

        accum.append("addr ")
        accum.append(EtherAddress(status.sta).to_str())
        accum.append(" net_bssid ")
        accum.append(EtherAddress(status.net_bssid).to_str())
        accum.append(" lvap_bssid ")
        accum.append(EtherAddress(status.lvap_bssid).to_str())

        accum.append(" ssid ")

        if incoming_ssids[0]:
            accum.append(incoming_ssids[0].to_str())
        else:
            accum.append("None")

        accum.append(" ssids [")

        for ssid in incoming_ssids[1:]:
            accum.append(" ")
            accum.append(ssid.to_str())

        accum.append(" ]")

        accum.append(" assoc_id ")
        accum.append(str(status.assoc_id))

        if bool(status.flags.authenticated):
            accum.append(" AUTH")

        if bool(status.flags.associated):
            accum.append(" ASSOC")

        LOG.info("LVAP status %s", ''.join(accum))

        # If the LVAP does not exists, then create a new one
        if sta not in RUNTIME.lvaps:

            net_bssid_addr = EtherAddress(status.net_bssid)
            lvap_bssid_addr = EtherAddress(status.lvap_bssid)
            lvap = LVAP(sta, net_bssid_addr, lvap_bssid_addr)

            RUNTIME.lvaps[sta] = lvap

        lvap = RUNTIME.lvaps[sta]

        # Check if block is valid
        incoming = ResourceBlock(wtp, EtherAddress(status.hwaddr),
                                 status.channel, status.band)

        valid = [block for block in wtp.supports if block == incoming]

        if not valid:
            LOG.warning("No valid intersection found. Removing block.")
            wtp.connection.send_del_lvap(lvap)
            return

        # this will try to updated the lvap object with the resource block
        # coming in this status update message.
        try:
            if set_mask:
                # set downlink+uplink block
                lvap._downlink.setitem(valid[0], RadioPort(lvap, valid[0]))
            else:
                # set uplink only blocks
                lvap._uplink.setitem(valid[0], RadioPort(lvap, valid[0]))
        except Exception as e:
            LOG.exception(e)
            LOG.error("Error while importing block %s, removing.", valid[0])
            wtp.connection.send_del_lvap(lvap)
            return

        # update LVAP ports
        lvap.ports[0] = VirtualPortLvap(phy_port=wtp.port(),
                                        virtual_port_id=0,
                                        lvap=lvap)

        # set supported band
        lvap.supported_band = status.supported_band

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
                LOG.info("Removing %s from tenant %s", lvap.addr, lvap.ssid)
                del lvap.tenant.lvaps[lvap.addr]

            lvap._tenant = None

        # update remaining ssids
        lvap._ssids = ssids[1:]

        if ssids[0]:

            tenant = RUNTIME.load_tenant(ssids[0])

            if not tenant:
                LOG.info("LVAP %s from unknown tenant %s", lvap.addr, ssids[0])
                RUNTIME.remove_lvap(lvap.addr)
                return

            # setting tenant without seding out add lvap message
            lvap._tenant = tenant

            # adding LVAP to tenant
            LOG.info("Adding %s to tenant %s", lvap.addr, ssids[0])
            lvap.tenant.lvaps[lvap.addr] = lvap

            # Raise LVAP join event
            self.server.send_lvap_join_message_to_self(lvap)

    @classmethod
    def _handle_status_port(cls, wtp, status):
        """Handle an incoming PORT message.
        Args:
            status, a STATUS_PORT message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", wtp.addr)
            return

        sta_addr = EtherAddress(status.sta)

        # incoming block
        incoming = ResourceBlock(wtp, EtherAddress(status.hwaddr),
                                 status.channel, status.band)

        valid = [block for block in wtp.supports if block == incoming]

        if not valid:
            LOG.error("Incoming block %s is invalid", incoming)
            return

        block = valid[0]

        LOG.info("Port status from %s, station %s", wtp.addr, sta_addr)

        tx_policy = block.tx_policies[sta_addr]

        tx_policy._mcs = set([float(x) / 2 for x in status.mcs])
        tx_policy._ht_mcs = set([int(x) for x in status.ht_mcs])
        tx_policy._rts_cts = int(status.rts_cts)
        tx_policy._mcast = int(status.tx_mcast)
        tx_policy._ur_count = int(status.ur_mcast_count)
        tx_policy._no_ack = bool(status.flags.no_ack)

        LOG.info("Port status %s", tx_policy)

    def _handle_caps(self, wtp, caps):
        """Handle an incoming CAPS message.
        Args:
            caps, a CAPS message
        Returns:
            None
        """

        LOG.info("Received caps from %s", wtp.addr)

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
    def _handle_interference_map(cls, wtp, interference_map):
        """Handle an incoming INTERFERENCE_MAP message.
        Args:
            interference_map, an INTERFERENCE_MAP message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("Status from disconnected WTP %s", wtp.addr)
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
    def _handle_status_vap(cls, wtp, status):
        """Handle an incoming STATUS_VAP message.
        Args:
            status, a STATUS_VAP message
        Returns:
            None
        """

        if not wtp.connection:
            LOG.info("VAP Status from disconnected WTP %s", wtp.addr)
            return

        net_bssid_addr = EtherAddress(status.net_bssid)
        ssid = SSID(status.ssid)
        tenant = RUNTIME.load_tenant(ssid)

        if not tenant:
            LOG.info("VAP %s from unknown tenant %s", net_bssid_addr, ssid)
            return

        incoming = ResourceBlock(wtp, EtherAddress(status.hwaddr),
                                 status.channel, status.band)

        LOG.info("VAP status update from %s", net_bssid_addr)

        # If the VAP does not exists, then create a new one
        if net_bssid_addr not in tenant.vaps:
            vap = VAP(net_bssid_addr, incoming, wtp, tenant)
            tenant.vaps[net_bssid_addr] = vap

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
                            length=24,
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

    def send_del_vap(self, vap):
        """Send a DEL_VAP message.
        Args:
            vap: an VAP object
        Returns:
            None
        Raises:
            TypeError: if vap is not an VAP object
        """

        del_vap = Container(version=PT_VERSION,
                            type=PT_DEL_VAP,
                            length=16,
                            seq=self.wtp.seq,
                            net_bssid=vap.net_bssid.to_raw())

        LOG.info("Del vap %s", vap)

        msg = DEL_VAP.build(del_vap)
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
                             length=16,
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
                             length=22,
                             seq=self.wtp.seq,
                             sta=lvap.addr.to_raw(),
                             bssid=lvap.lvap_bssid.to_raw())

        msg = AUTH_RESPONSE.build(response)
        self.stream.write(msg)

    def send_probe_response(self, lvap, ssid):
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
                             length=16 + len(ssid.to_raw()),
                             seq=self.wtp.seq,
                             sta=lvap.addr.to_raw(),
                             ssid=ssid.to_raw())

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

        target_block = lvap.target_block

        target_hwaddr = EtherAddress.bcast()
        target_channel = 0
        target_band = 0

        if target_block:
            target_hwaddr = target_block.hwaddr
            target_channel = target_block.channel
            target_band = target_block.band

        del_lvap = Container(version=PT_VERSION,
                             type=PT_DEL_LVAP,
                             length=30,
                             seq=self.wtp.seq,
                             module_id=lvap.module_id,
                             sta=lvap.addr.to_raw(),
                             target_hwaddr=target_hwaddr.to_raw(),
                             target_channel=target_channel,
                             tagert_band=target_band,
                             csa_switch_mode=0,
                             csa_switch_count=3)

        LOG.info("Del lvap %s", lvap)

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
        ht_rates = sorted([int(x) for x in tx_policy.ht_mcs])

        set_port = Container(version=PT_VERSION,
                             type=PT_SET_PORT,
                             length=32 + len(rates) + len(ht_rates),
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
                             nb_ht_mcses=len(ht_rates),
                             mcs=rates,
                             ht_mcs=ht_rates)

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
                             length=51,
                             seq=self.wtp.seq,
                             module_id=lvap.module_id,
                             flags=flags,
                             assoc_id=lvap.assoc_id,
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
