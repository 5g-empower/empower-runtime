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

"""LVAPP Connection."""

import time

from random import randint

from construct import Container
from tornado.iostream import StreamClosedError

from empower.core.launcher import srv_or_die
from empower.managers.ranmanager.lvapp.txpolicy import TxPolicy
from empower.core.etheraddress import EtherAddress
from empower.managers.ranmanager.lvapp.resourcepool import ResourceBlock
from empower.core.ssid import SSID, WIFI_NWID_MAXSIZE
from empower.managers.ranmanager.lvapp.lvap import LVAP, PROCESS_RUNNING
from empower.managers.ranmanager.lvapp.vap import VAP
from empower.managers.projectsmanager.project import T_BSSID_TYPE_SHARED
from empower.managers.projectsmanager.project import T_BSSID_TYPE_UNIQUE
from empower.managers.ranmanager.ranconnection import RANConnection

HELLO_PERIOD = 2000
HB_PERIOD = 500


class LVAPPConnection(RANConnection):
    """A persistent connection to a RAN device."""

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
        if hdr.type not in self.proto.PT_TYPES:
            self.log.warning("Unknown message type %u, ignoring.", hdr.type)
            return

        # Check if the Device is among the ones we known
        addr = EtherAddress(hdr.device)

        if addr not in self.manager.devices:
            self.log.warning("Unknown Device %s, closing connection.", addr)
            self.stream.close()
            return

        device = self.manager.devices[addr]

        # Log message informations
        parser = self.proto.PT_TYPES[hdr.type]
        msg = parser.parse(self.buffer)
        self.log.debug("Got %s message from %s seq %u", parser.name,
                       EtherAddress(addr), hdr.seq)

        # If Device is not online and is not connected, then the only message
        # type we can accept is HELLO_RESPONSE
        if not device.is_connected():

            if msg.type != self.proto.PT_HELLO_REQUEST:
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
            valid = (self.proto.PT_HELLO_REQUEST, self.proto.PT_CAPS_RESPONSE)
            if msg.type not in valid:
                if not self.stream.closed():
                    self.wait()
                return

        # Otherwise handle message
        try:
            method = self.proto.PT_TYPES[msg.type].name
            self.handle_message(method, msg)
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
        if msg.type in self.proto.PT_TYPES_HANDLERS:
            for handler in self.proto.PT_TYPES_HANDLERS[msg.type]:
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

        # Remove hosted LVAPs
        lvaps = [lvap for lvap in self.manager.lvaps.values()
                 if lvap.wtp.addr == self.device.addr]

        for lvap in list(lvaps):
            del self.manager.lvaps[lvap.addr]
            lvap.clear_blocks()

        # remove hosted VAPs
        vaps = [vap for vap in self.manager.vaps.values()
                if vap.block.wtp.addr == self.device.addr]

        for vap in list(vaps):
            del self.manager.vaps[vap.bssid]
            vap.clear_block()

        # reset state
        self.device.set_disconnected()
        self.device.last_seen = 0
        self.device.connection = None
        self.device.blocks = {}
        self.device = None

        # Stop hb worker
        self.hb_worker.stop()

    def send_message(self, msg_type, msg, callback=None):
        """Send message and set common parameters."""

        parser = self.proto.PT_TYPES[msg_type]

        if self.stream.closed():
            self.log.warning("Stream closed, unabled to send %s message to %s",
                             parser.name, self.device)
            return 0

        msg.version = self.proto.PT_VERSION
        msg.seq = self.seq
        msg.type = msg_type
        msg.xid = self.xid

        if not self.device:
            msg.device = EtherAddress("00:00:00:00:00:00").to_raw()
        else:
            msg.device = self.device.addr.to_raw()

        addr = self.stream.socket.getpeername()

        self.log.debug("Sending %s message to %s seq %u",
                       parser.name, addr[0], msg.seq)

        self.stream.write(parser.build(msg))

        if callback:
            self.xids[msg.xid] = (msg, callback)

        return msg.xid

    def update_vaps(self):
        """Update active VAPs."""

        for project in srv_or_die("projectsmanager").projects.values():

            # project does not have wifi_props
            if not project.wifi_props:
                continue

            # project does not use shared VAPs
            if project.wifi_props.bssid_type == T_BSSID_TYPE_UNIQUE:
                continue

            for block in self.device.blocks.values():

                bssid = project.generate_bssid(block.hwaddr)

                # vap has already been created
                if bssid in self.manager.vaps:
                    continue

                vap = VAP(bssid, block, project.wifi_props.ssid)

                self.send_add_vap(vap)

                self.manager.vaps[bssid] = vap

    def update_slices(self):
        """Update active Slices."""

        # send slices configuration
        for project in srv_or_die("projectsmanager").projects.values():

            # project does not have wifi_props
            if not project.wifi_props:
                continue

            for slc in project.wifi_slices.values():
                for block in self.device.blocks.values():
                    self.device.connection.send_set_slice(project, slc, block)

    def _handle_hello_request(self, hello):
        """Handle an incoming HELLO_RESPONSE message."""

        self.device.last_seen = hello.seq
        self.device.last_seen_ts = time.time()

        self.send_hello_response(hello.period)

    def _handle_caps_response(self, caps):
        """Handle an incoming CAPS message."""

        for block in caps.blocks:

            self.device.blocks[block.block_id] = \
                ResourceBlock(self.device,
                              block.block_id,
                              EtherAddress(block.hwaddr),
                              block.channel,
                              block.band)

        # set state to online
        self.device.set_online()

        # fetch active lvaps
        self.send_lvap_status_request()

        # fetch active vaps
        self.send_vap_status_request()

        # fetch active traffic rules
        self.send_slice_status_request()

        # fetch active tramission policies
        self.send_tx_policy_status_request()

        # send vaps
        self.update_vaps()

        # send slices
        self.update_slices()

    def _handle_probe_request(self, request):
        """Handle an incoming PROBE_REQUEST message."""

        # Get station
        sta = EtherAddress(request.sta)

        # Incoming
        incoming_ssid = SSID(request.ssid)
        iface_id = request.iface_id
        ht_caps = request.flags.ht_caps
        ht_caps_info = dict(request.ht_caps_info)
        del ht_caps_info['_io']

        block = self.device.blocks[request.iface_id]

        msg = "Probe request from %s ssid %s iface_id %u ht_caps %u"

        if not incoming_ssid:
            self.log.debug(msg, sta, "Broadcast", iface_id, ht_caps)
        else:
            self.log.debug(msg, sta, incoming_ssid, iface_id, ht_caps)

        # Check is station is in ACL of any networks
        networks = \
            srv_or_die("projectsmanager").get_available_ssids(sta, block)

        if not networks:
            self.log.debug("No SSID available at this device")
            return

        # If lvap does not exist then create it. Otherwise just refresh the
        # list of available networks
        if sta not in self.manager.lvaps:

            # spawn new LVAP
            self.log.info("Spawning new LVAP %s on %s", sta, self.device.addr)

            assoc_id = randint(1, 2007)

            lvap = LVAP(sta, assoc_id=assoc_id)
            lvap.networks = networks
            lvap.ht_caps = ht_caps
            lvap.ht_caps_info = ht_caps_info

            # this will trigger an LVAP ADD message
            lvap.blocks = block

            # save LVAP in the runtime
            self.manager.lvaps[sta] = lvap

            # Send probe response
            self.send_probe_response(lvap, incoming_ssid)

            return

        lvap = self.manager.lvaps[sta]

        # If this probe request is not coming from the same interface on which
        # this LVAP is currenly running then ignore the probe
        if lvap.blocks[0] != block:
            return

        # If LVAP is not running then ignore
        if not lvap.is_running():
            return

        # Update list of available networks
        lvap.networks = networks
        lvap.commit()

        # Send probe response
        self.send_probe_response(lvap, incoming_ssid)

    def _handle_auth_request(self, request):
        """Handle an incoming AUTH_REQUEST message."""

        sta = EtherAddress(request.sta)

        if sta not in self.manager.lvaps:
            self.log.info("Auth request from unknown LVAP %s", sta)
            return

        lvap = self.manager.lvaps[sta]

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
        for project in srv_or_die("projectsmanager").projects.values():

            if not project.wifi_props:
                continue

            if project.wifi_props.bssid_type == T_BSSID_TYPE_SHARED:
                continue

            bssid = project.generate_bssid(lvap.addr)

            if bssid == incoming_bssid:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = False
                lvap.ssid = None
                lvap.commit()
                self.send_auth_response(lvap)
                return

        # Finally check if this is a shared bssid
        for project in srv_or_die("projectsmanager").projects.values():

            if not project.wifi_props:
                continue

            if project.wifi_props.bssid_type == T_BSSID_TYPE_UNIQUE:
                continue

            if incoming_bssid in project.vaps:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = False
                lvap.ssid = None
                lvap.commit()
                self.send_auth_response(lvap)
                return

        self.log.info("Auth request from unknown BSSID %s", incoming_bssid)

    def _handle_assoc_request(self, request):
        """Handle an incoming ASSOC_REQUEST message."""

        sta = EtherAddress(request.sta)

        ht_caps = request.flags.ht_caps
        ht_caps_info = dict(request.ht_caps_info)
        del ht_caps_info['_io']

        if sta not in self.manager.lvaps:
            self.log.info("Assoc request from unknown LVAP %s", sta)
            return

        lvap = self.manager.lvaps[sta]

        incoming_bssid = EtherAddress(request.bssid)

        if lvap.bssid != incoming_bssid:
            self.log.info("Assoc request for invalid BSSID %s", incoming_bssid)
            return

        incoming_ssid = SSID(request.ssid)

        # Check if the requested SSID is from a unique project
        for project in srv_or_die("projectsmanager").projects.values():

            if not project.wifi_props:
                continue

            if project.wifi_props.bssid_type == T_BSSID_TYPE_SHARED:
                continue

            bssid = project.generate_bssid(lvap.addr)

            if bssid != incoming_bssid:
                self.log.info("Invalid BSSID %s", incoming_bssid)
                continue

            if project.wifi_props.ssid == incoming_ssid:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = True
                lvap.ssid = incoming_ssid
                lvap.ht_caps = ht_caps
                lvap.ht_caps_info = ht_caps_info
                lvap.commit()
                self.send_assoc_response(lvap)
                return

        # Check if the requested SSID is from a unique project
        for project in srv_or_die("projectsmanager").projects.values():

            if not project.wifi_props:
                continue

            if project.wifi_props.bssid_type == T_BSSID_TYPE_UNIQUE:
                continue

            if incoming_bssid not in project.vaps:
                self.log.info("Invalid BSSID %s", incoming_bssid)
                continue

            if project.wifi_props.ssid == incoming_ssid:
                lvap.bssid = incoming_bssid
                lvap.authentication_state = True
                lvap.association_state = True
                lvap.ssid = incoming_ssid
                lvap.ht_caps = ht_caps
                lvap.ht_caps_info = ht_caps_info
                lvap.commit()
                self.send_assoc_response(lvap)
                return

        self.log.info("Unable to find SSID %s", incoming_ssid)

    def _handle_lvap_status_response(self, status):
        """Handle an incoming LVAP_STATUS_RESPONSE message."""

        sta = EtherAddress(status.sta)

        # If the LVAP does not exists, then create a new one
        if sta not in self.manager.lvaps:
            self.manager.lvaps[sta] = \
                LVAP(sta, assoc_id=status.assoc_id, state=PROCESS_RUNNING)

        lvap = self.manager.lvaps[sta]

        # update LVAP params
        lvap.encap = EtherAddress(status.encap)
        lvap.authentication_state = bool(status.flags.authenticated)
        lvap.association_state = bool(status.flags.associated)
        lvap.ht_caps = bool(status.flags.ht_caps)
        lvap.ht_caps_info = dict(status.ht_caps_info)
        del lvap.ht_caps_info['_io']

        ssid = SSID(status.ssid)
        if ssid == SSID():
            ssid = None

        bssid = EtherAddress(status.bssid)
        if bssid == EtherAddress("00:00:00:00:00:00"):
            bssid = None

        lvap.bssid = bssid

        incoming = self.device.blocks[status.iface_id]

        if status.flags.set_mask:
            lvap.downlink = incoming
        else:
            lvap.uplink.append(incoming)

        # if this is not a DL+UL block then stop here
        if not status.flags.set_mask:
            return

        # if an SSID is set and the incoming SSID is different from the
        # current one then raise an LVAP leave event
        if lvap.ssid and ssid != lvap.ssid:
            self.send_client_leave_message_to_self(lvap)
            lvap.ssid = None

        # if the incoming ssid is not none then raise an lvap join event
        if ssid:
            lvap.ssid = ssid
            self.send_client_join_message_to_self(lvap)

        # udpate networks
        networks = list()

        for network in status.networks:
            incoming = (EtherAddress(network.bssid), SSID(network.ssid))
            networks.append(incoming)

        lvap.networks = networks

        self.log.info("LVAP status: %s", lvap)

    def _handle_tx_policy_status_response(self, status):
        """Handle an incoming TX_POLICY_STATUS_RESPONSE message."""

        block = self.device.blocks[status.iface_id]
        addr = EtherAddress(status.sta)

        if addr not in block.tx_policies:
            block.tx_policies[addr] = TxPolicy(addr, block)

        txp = block.tx_policies[addr]

        txp.set_mcs([float(x) / 2 for x in status.mcs])
        txp.set_ht_mcs([int(x) for x in status.mcs_ht])
        txp.set_rts_cts(status.rts_cts)
        txp.set_max_amsdu_len(status.max_amsdu_len)
        txp.set_mcast(status.tx_mcast)
        txp.set_no_ack(status.flags.no_ack)

        self.log.info("TX policy status: %s", txp)

    def _handle_slice_status_response(self, status):
        """Handle an incoming SLICE_STATUS_RESPONSE message."""

        iface_id = status.iface_id
        slice_id = str(status.slice_id)
        ssid = SSID(status.ssid)

        project = srv_or_die("projectsmanager").load_project_by_ssid(ssid)
        block = self.device.blocks[iface_id]

        if not project:
            self.log.warning("Slice status from unknown SSID %s", ssid)
            return

        if slice_id not in project.wifi_slices:
            self.log.warning("Slice %s not found. Removing slice.", slice_id)
            self.send_del_slice(project, int(slice_id), block)
            return

        slc = project.wifi_slices[slice_id]

        if slc.properties['quantum'] != status.quantum:
            if self.device.addr not in slc.devices:
                slc.devices[self.device.addr] = dict()
            slc.devices[self.device.addr]['quantum'] = status.quantum

        amsdu_aggregation = bool(status.flags.amsdu_aggregation)
        if slc.properties['amsdu_aggregation'] != amsdu_aggregation:
            if self.device.addr not in slc.devices:
                slc.devices[self.device.addr] = dict()
            slc.devices[self.device.addr]['amsdu_aggregation'] = \
                amsdu_aggregation

        if slc.properties['sta_scheduler'] != status.sta_scheduler:
            if self.device.addr not in slc.devices:
                slc.devices[self.device.addr] = dict()
            slc.devices[self.device.addr]['sta_scheduler'] = \
                status.sta_scheduler

        project.save()
        project.refresh_from_db()

        self.log.info("Slice status: %s", slc)

    def _handle_vap_status_response(self, status):
        """Handle an incoming STATUS_VAP message."""

        bssid = EtherAddress(status.bssid)
        ssid = SSID(status.ssid)

        project = srv_or_die("projectsmanager").load_project_by_ssid(ssid)

        if not project:
            self.log.warning("Unable to find SSID %s", ssid)
            self.send_del_vap(bssid)
            return

        # If the VAP does not exists, then create a new one
        if bssid not in self.manager.vaps:

            incoming = self.device.blocks[status.iface_id]

            self.manager.vaps[bssid] = VAP(bssid, incoming,
                                           project.wifi_props.ssid)

        vap = self.manager.vaps[bssid]

        self.log.info("VAP status: %s", vap)

    def send_hello_response(self, period=2000):
        """Send a HELLO_REQUEST message."""

        msg = Container(length=self.proto.HELLO_RESPONSE.sizeof(),
                        period=period)

        return self.send_message(self.proto.PT_HELLO_RESPONSE, msg)

    def send_caps_request(self):
        """Send a CAPS_REQUEST message."""

        msg = Container(length=self.proto.CAPS_REQUEST.sizeof())
        return self.send_message(self.proto.PT_CAPS_REQUEST, msg)

    def send_lvap_status_request(self):
        """Send a LVAP_STATUS_REQUEST message."""

        msg = Container(length=self.proto.LVAP_STATUS_REQUEST.sizeof())
        return self.send_message(self.proto.PT_LVAP_STATUS_REQUEST, msg)

    def send_vap_status_request(self):
        """Send a VAP_STATUS_REQUEST message."""

        msg = Container(length=self.proto.VAP_STATUS_REQUEST.sizeof())
        return self.send_message(self.proto.PT_VAP_STATUS_REQUEST, msg)

    def send_slice_status_request(self):
        """Send a PT_SLICE_STATUS_REQUEST message."""

        msg = Container(length=self.proto.SLICE_STATUS_REQUEST.sizeof())
        return self.send_message(self.proto.PT_SLICE_STATUS_REQUEST, msg)

    def send_tx_policy_status_request(self):
        """Send a TRANSMISSION_POLICY_STATUS_REQUEST message."""

        msg = Container(length=self.proto.TX_POLICY_STATUS_REQUEST.sizeof())
        return self.send_message(self.proto.PT_TX_POLICY_STATUS_REQUEST, msg)

    def send_add_vap(self, vap):
        """Send a ADD_VAP message."""

        msg = Container(length=self.proto.ADD_VAP.sizeof(),
                        iface_id=vap.block.block_id,
                        bssid=vap.bssid.to_raw(),
                        ssid=vap.ssid.to_raw())

        return self.send_message(self.proto.PT_ADD_VAP, msg)

    def send_del_vap(self, bssid):
        """Send a DEL_VAP message."""

        msg = Container(length=self.proto.DEL_VAP.sizeof(),
                        bssid=bssid.to_raw())
        return self.send_message(self.proto.PT_DEL_VAP, msg)

    def send_assoc_response(self, lvap):
        """Send a ASSOC_RESPONSE message."""

        msg = Container(length=self.proto.ASSOC_RESPONSE.sizeof(),
                        sta=lvap.addr.to_raw())
        return self.send_message(self.proto.PT_ASSOC_RESPONSE, msg)

    def send_auth_response(self, lvap):
        """Send a AUTH_RESPONSE message."""

        msg = Container(length=self.proto.AUTH_RESPONSE.sizeof(),
                        sta=lvap.addr.to_raw(),
                        bssid=lvap.bssid.to_raw())

        return self.send_message(self.proto.PT_AUTH_RESPONSE, msg)

    def send_probe_response(self, lvap, ssid):
        """Send a PROBE_RESPONSE message."""

        msg = Container(length=self.proto.PROBE_RESPONSE.sizeof(),
                        sta=lvap.addr.to_raw(),
                        ssid=ssid.to_raw())

        return self.send_message(self.proto.PT_PROBE_RESPONSE, msg)

    def send_set_tx_policy(self, txp):
        """Send a SET_TX_POLICY message."""

        flags = Container(no_ack=txp.no_ack)
        rates = sorted([int(x * 2) for x in txp.mcs])
        ht_rates = sorted([int(x) for x in txp.ht_mcs])

        msg = Container(length=39 + len(rates) + len(ht_rates),
                        flags=flags,
                        sta=txp.addr.to_raw(),
                        iface_id=txp.block.block_id,
                        rts_cts=txp.rts_cts,
                        max_amsdu_len=txp.max_amsdu_len,
                        tx_mcast=txp.mcast,
                        ur_count=txp.ur_count,
                        nb_mcses=len(rates),
                        nb_ht_mcses=len(ht_rates),
                        mcs=rates,
                        mcs_ht=ht_rates)

        return self.send_message(self.proto.PT_SET_TX_POLICY, msg)

    def send_del_tx_policy(self, txp):
        """Send a DEL_TX_POLICY message."""

        msg = Container(length=self.proto.DEL_TX_POLICY.sizeof(),
                        sta=txp.addr.to_raw(),
                        hwaddr=txp.block.hwaddr.to_raw(),
                        channel=txp.block.channel,
                        band=txp.block.band)

        return self.send_message(self.proto.PT_DEL_TX_POLICY, msg)

    def send_add_lvap_request(self, lvap, block, set_mask):
        """Send a ADD_LVAP message."""

        flags = Container(ht_caps=lvap.ht_caps,
                          authenticated=lvap.authentication_state,
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

        msg = Container(length=80,
                        flags=flags,
                        assoc_id=lvap.assoc_id,
                        iface_id=block.block_id,
                        ht_caps_info=Container(**lvap.ht_caps_info),
                        sta=lvap.addr.to_raw(),
                        encap=encap.to_raw(),
                        bssid=bssid.to_raw(),
                        ssid=ssid.to_raw(),
                        networks=[])

        for network in lvap.networks:
            msg.length = msg.length + 6 + WIFI_NWID_MAXSIZE + 1
            msg.networks.append(Container(bssid=network[0].to_raw(),
                                          ssid=network[1].to_raw()))

        return self.send_message(self.proto.PT_ADD_LVAP_REQUEST, msg,
                                 lvap.handle_add_lvap_response)

    def send_del_lvap_request(self, lvap, csa_switch_channel=0):
        """Send a DEL_LVAP message."""

        msg = Container(length=self.proto.DEL_LVAP_REQUEST.sizeof(),
                        sta=lvap.addr.to_raw(),
                        csa_switch_mode=0,
                        csa_switch_count=3,
                        csa_switch_channel=csa_switch_channel)

        return self.send_message(self.proto.PT_DEL_LVAP_REQUEST, msg,
                                 lvap.handle_del_lvap_response)

    def send_set_slice(self, project, slc, block):
        """Send an SET_SLICE message."""

        ssid = project.wifi_props.ssid

        amsdu_aggregation = slc.properties['amsdu_aggregation']
        quantum = slc.properties['quantum']
        sta_scheduler = slc.properties['sta_scheduler']

        if self.device.addr in slc.devices:

            properties = slc.devices[self.device.addr]

            if 'amsdu_aggregation' in properties:
                amsdu_aggregation = properties['amsdu_aggregation']

            if 'quantum' in properties:
                quantum = properties['quantum']

            if 'sta_scheduler' in properties:
                sta_scheduler = properties['sta_scheduler']

        flags = Container(amsdu_aggregation=amsdu_aggregation)

        msg = Container(length=self.proto.SET_SLICE.sizeof(),
                        flags=flags,
                        iface_id=block.block_id,
                        quantum=quantum,
                        sta_scheduler=sta_scheduler,
                        slice_id=slc.slice_id,
                        ssid=ssid.to_raw())

        return self.send_message(self.proto.PT_SET_SLICE, msg)

    def send_del_slice(self, project, slice_id, block):
        """Send an DEL_SLICEs message. """

        ssid = project.wifi_props.ssid

        msg = Container(length=self.proto.DEL_SLICE.sizeof(),
                        iface_id=block.block_id,
                        slice_id=slice_id,
                        ssid=ssid.to_raw())

        return self.send_message(self.proto.PT_DEL_SLICE, msg)
