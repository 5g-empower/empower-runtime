#!/usr/bin/env python3
#
# Copyright (c) 2018 Giovanni Baggio

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

"""IBN Protocol Server."""

import time
import json

from uuid import uuid4

import tornado.websocket

from empower.datatypes.dpid import DPID
from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.match import Match
from empower.core.jsonserializer import EmpowerEncoder
from empower.core.networkport import NetworkPort
from empower.core.datapath import Datapath
from empower.core.endpoint import Endpoint
from empower.core.virtualport import VirtualPort

from empower.ibnp import PT_VERSION
from empower.ibnp import PT_UPDATE_ENDPOINT
from empower.ibnp import PT_REMOVE_ENDPOINT
from empower.ibnp import PT_ADD_RULE
from empower.ibnp import PT_REMOVE_RULE

from empower.core.utils import get_module
from empower.lvapp.lvappserver import LVAPPServer
from empower.lvapp import PT_LVAP_JOIN
from empower.lvapp import PT_LVAP_LEAVE
from empower.lvapp import PT_LVAP_HANDOVER

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class IBNPMainHandler(tornado.websocket.WebSocketHandler):

    HANDLERS = [r"/"]

    def initialize(self, server):

        self.server = server

        self.of_dpid = []
        self.dpid2ep = {}
        self.of_rules = {}

        # map from dscp values to tos
        self.dscp2tos = {'0x00': '0x00',
                         '0x01': '0x04',
                         '0x02': '0x08',
                         '0x03': '0x0C',
                         '0x04': '0x10',
                         '0x08': '0x20',
                         '0x0A': '0x28',
                         '0x0C': '0x30',
                         '0x0E': '0x38',
                         '0x10': '0x40',
                         '0x12': '0x48',
                         '0x14': '0x50',
                         '0x16': '0x58',
                         '0x18': '0x60',
                         '0x1A': '0x68',
                         '0x1C': '0x70',
                         '0x1E': '0x78',
                         '0x20': '0x80',
                         '0x22': '0x88',
                         '0x24': '0x90',
                         '0x26': '0x98',
                         '0x28': '0xA0',
                         '0x2C': '0xB0',
                         '0x2E': '0xB8',
                         '0x30': '0xC0',
                         '0x38': '0xE0'}

        lvapp_server = get_module(LVAPPServer.__module__)
        lvapp_server.register_message(PT_LVAP_JOIN, None, self._lvap_join)
        lvapp_server.register_message(PT_LVAP_LEAVE, None, self._lvap_leave)
        lvapp_server.register_message(PT_LVAP_HANDOVER,
                                      None,
                                      self._lvap_handover)

    def send_add_tr(self, tr):

        tenant_id = tr.tenant.tenant_id
        tenant = RUNTIME.tenants[tenant_id]

        for lvap in tenant.lvaps.values():

            self._send_add_tr(tenant, lvap, tr.match, tr.dscp, tr.priority)

    def send_remove_tr(self, tenant_id, match):

        tenant = RUNTIME.tenants[tenant_id]

        if tenant_id not in self.of_rules:
            return

        tenant_rules = self.of_rules[tenant.tenant_id]

        tr_rule_ids = [(match, _) for _match, _ in tenant_rules
                       if _match == match]

        for tr_rule_id in tr_rule_ids:

            of_rule_id = tenant_rules[tr_rule_id]
            self.send_remove_rule(of_rule_id)
            del tenant_rules[tr_rule_id]

    def _lvap_join(self, lvap):

        tenant = lvap.tenant

        if not self.server.connection:
            return

        if tenant.tenant_id not in self.server.rules:
            return

        tenant_rules = self.server.rules[tenant.tenant_id]

        if lvap.tenant.tenant_id not in self.of_rules:
            self.of_rules[tenant.tenant_id] = {}

        tenant_of_rules = self.of_rules[tenant.tenant_id]

        for tr in tenant_rules.values():

            if (tr.match, lvap.addr) in tenant_of_rules:
                continue

            self._send_add_tr(tenant=tenant,
                              lvap=lvap,
                              match=tr.match,
                              dscp=tr.dscp,
                              priority=tr.priority)

    def _lvap_leave(self, lvap):

        if lvap.tenant.tenant_id not in self.of_rules:
            return

        tenant_rules = self.of_rules[lvap.tenant.tenant_id]

        tr_rule_ids = [(_, _lvap_addr) for _, _lvap_addr in tenant_rules
                       if _lvap_addr == lvap.addr]

        for tr_rule_id in tr_rule_ids:

            of_rule_id = tenant_rules[tr_rule_id]
            self.send_remove_rule(of_rule_id)
            del tenant_rules[tr_rule_id]

    def _lvap_handover(self, lvap, _):

        # ignore handover events if the lvap is not associated
        if lvap.tenant:
            self._lvap_leave(lvap)
            self._lvap_join(lvap)

    def _of_dp_join(self, dp):

        wtp_addr = EtherAddress(str(dp.dpid)[6:])

        if wtp_addr not in RUNTIME.wtps:
            return

        for lvap in RUNTIME.lvaps.values():

            if lvap.wtp.addr != wtp_addr:
                continue

            if lvap.tenant is None:
                continue

            self._lvap_join(lvap)

    def _send_add_tr(self, tenant, lvap, match, dscp, priority):

        dp = lvap.wtp.datapath

        if dp.dpid not in self.of_dpid:
            return None

        if dp.dpid not in self.dpid2ep:

            tr_ep = Endpoint(uuid4(), '', dp)

            if dp.network_ports.keys() != {1, 2}:
                raise ValueError('Network port numbers mismatch, '
                                 'please restart the WTP')

            src_vport = VirtualPort(tr_ep, dp.network_ports[1], 0)
            dst_vport = VirtualPort(tr_ep, dp.network_ports[2], 1)

            tr_ep.ports[src_vport.virtual_port_id] = src_vport
            tr_ep.ports[dst_vport.virtual_port_id] = dst_vport

            self.dpid2ep[dp.dpid] = tr_ep

        tr_ep = self.dpid2ep[dp.dpid]

        of_rule_id = uuid4()

        sta_match = Match('%s,dl_dst=%s' % (str(match), lvap.addr))

        rule = {'version': '1.0',
                'uuid': of_rule_id,
                'ttp_uuid': tr_ep.uuid,
                'ttp_vport': tr_ep.ports[1].virtual_port_id,
                'stp_uuid': tr_ep.uuid,
                'stp_vport': tr_ep.ports[0].virtual_port_id,
                'match': sta_match.match,
                'actions': [{'type': 'SET_NW_TOS',
                             'nw_tos': self.dscp2tos[str(dscp)]}],
                'priority': priority}

        self.send_add_rule(rule)

        tr_id = (match, lvap.addr)

        if tenant.tenant_id not in self.of_rules:
            self.of_rules[tenant.tenant_id] = {}

        self.of_rules[tenant.tenant_id][tr_id] = of_rule_id

    def open(self):
        """On socket opened."""

        pass

    def encode_message(self, message):
        """Encode JSON message."""

        self.write_message(json.dumps(message, cls=EmpowerEncoder))

    def on_message(self, message):
        """Handle incoming message."""

        try:
            msg = json.loads(message)
            self.handle_message(msg)
        except ValueError:
            LOG.error("Invalid input: %s", message)

    def handle_tr_events(self, event_type, data):

        if not self.server.connection:
            return

    def handle_message(self, msg):
        """Handle incoming message."""

        LOG.info("Received %s seq %u from %s", msg['type'], msg['seq'],
                 self.request.remote_ip)

        handler_name = "_handle_%s" % msg['type']

        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            try:
                handler(msg)
            except Exception as ex:
                LOG.exception(ex)
                return
        else:
            LOG.error('Unknown handler %s', handler_name)

    def on_close(self):
        """ Handle IBN disconnection """

        if not self.server:
            return

        # reset state
        self.server.connection = None

    def send_message(self, message_type, message):
        """Add fixed header fields and send message. """

        message['version'] = PT_VERSION
        message['type'] = message_type
        message['seq'] = self.server.seq

        LOG.info("Sending %s seq %u", message['type'], message['seq'])
        self.write_message(json.dumps(message, cls=EmpowerEncoder))

    def _handle_hello(self, hello):
        """Handle an incoming IBNP_HELLO message.

        Args:
            hello, a HELLO message

        Returns:
            None
        """

        if not self.server.connection:
            self.server.connection = self

        LOG.info("Hello from IBN seq %u", hello['seq'])

        self.server.period = hello['every']
        self.server.last_seen = hello['seq']
        self.server.last_seen_ts = time.time()

    def _handle_new_datapath(self, of_datapath):

        dpid = DPID(of_datapath['dpid'])

        if dpid not in RUNTIME.datapaths:
            RUNTIME.datapaths[dpid] = Datapath(dpid)

        datapath = RUNTIME.datapaths[dpid]
        datapath.ip_addr = of_datapath['ip_addr']

        for port in of_datapath['ports']:

            port_id = port['port_no']

            if port_id not in datapath.network_ports:

                network_port = NetworkPort(dp=datapath,
                                           port_id=port['port_no'],
                                           hwaddr=port['hw_addr'],
                                           iface=port['name'])

                datapath.network_ports[port_id] = network_port

        if dpid not in self.of_dpid:
            self.of_dpid.append(dpid)

        self._of_dp_join(datapath)

    def _handle_new_link(self, of_link):

        of_port_src = of_link['src']
        src_dpid = DPID(of_port_src['dpid'])
        src_port_id = of_port_src['port_no']

        src_datapath = RUNTIME.datapaths[src_dpid]
        src_port = src_datapath.network_ports[src_port_id]

        of_port_dst = of_link['dst']
        dst_dpid = DPID(of_port_dst['dpid'])
        dst_port_id = of_port_dst['port_no']

        dst_datapath = RUNTIME.datapaths[dst_dpid]
        dst_port = dst_datapath.network_ports[dst_port_id]

        # links are unidirectional
        src_port.neighbour = dst_port

    def send_update_endpoint(self, endpoint):
        """Send update Endpoint"""

        self.send_message(PT_UPDATE_ENDPOINT, endpoint)

    def send_remove_endpoint(self, endpoint_uuid):

        remove_endpoint = {'uuid': endpoint_uuid}

        self.send_message(PT_REMOVE_ENDPOINT, remove_endpoint)

    def send_add_rule(self, rule):
        """Send add Rule"""

        self.send_message(PT_ADD_RULE, rule)

    def send_remove_rule(self, rule_uuid):

        remove_rule = {'uuid': rule_uuid}

        self.send_message(PT_REMOVE_RULE, remove_rule)
