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

import tornado.websocket

from empower.datatypes.dpid import DPID
from empower.core.jsonserializer import EmpowerEncoder
from empower.core.networkport import NetworkPort
from empower.core.datapath import Datapath

from empower.ibnp import PT_VERSION
from empower.ibnp import PT_UPDATE_ENDPOINT
from empower.ibnp import PT_REMOVE_ENDPOINT
from empower.ibnp import PT_ADD_RULE
from empower.ibnp import PT_REMOVE_RULE

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class IBNPMainHandler(tornado.websocket.WebSocketHandler):

    HANDLERS = [r"/"]

    def initialize(self, server):
        self.server = server

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

    def _handle_cleanup(self, cleanup):

        return

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

        remove_endpoint = {'endpoint_uuid': endpoint_uuid}

        self.send_message(PT_REMOVE_ENDPOINT, remove_endpoint)

    def send_add_rule(self, rule):
        """Send add Rule"""

        self.send_message(PT_ADD_RULE, rule)

    def send_remove_rule(self, rule_uuid):

        remove_rule = {'rule_uuid': rule_uuid}

        self.send_message(PT_REMOVE_RULE, remove_rule)
