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

"""LVNFP Protocol Server."""

import uuid
import time
import json
import tornado.web
import tornado.ioloop
import tornado.websocket

from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.dpid import DPID
from empower.core.jsonserializer import EmpowerEncoder
from empower.lvnfp import PT_ADD_LVNF
from empower.lvnfp import PT_DEL_LVNF
from empower.core.networkport import NetworkPort
from empower.core.virtualport import VirtualPort
from empower.core.datapath import Datapath
from empower.lvnfp import PT_BYE
from empower.lvnfp import PT_CAPS_RESPONSE
from empower.lvnfp import PT_HELLO
from empower.lvnfp import PT_REGISTER
from empower.lvnfp import PT_VERSION
from empower.lvnfp import PT_LVNF_STATUS_REQUEST
from empower.lvnfp import PT_CAPS_REQUEST
from empower.core.lvnf import LVNF
from empower.core.lvnf import PROCESS_RUNNING
from empower.core.image import Image
from empower.core.utils import get_xid

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class LVNFPMainHandler(tornado.websocket.WebSocketHandler):

    HANDLERS = [r"/"]

    def initialize(self, server):
        self.cpp = None
        self.addr = None
        self.server = server

    def to_dict(self):
        """Return dict representation of object."""

        return self.addr

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

        msg_type = msg['type']

        if msg_type not in self.server.pt_types:
            LOG.error("Unknown message type %s", msg_type)
            return

        addr = EtherAddress(msg['cpp'])

        try:
            cpp = RUNTIME.cpps[addr]
        except KeyError:
            LOG.error("Unknown CPP (%s), closing connection", addr)
            self.close()
            return

        valid = [PT_HELLO]
        if not cpp.connection and msg_type not in valid:
            LOG.info("Got %s message from disconnected %s seq %u",
                     msg_type, addr, msg['seq'])
            return

        LOG.info("Got %s message from %s seq %u xid %s",
                 msg_type, addr, msg['seq'], msg['xid'])

        if msg_type == PT_HELLO:
            self.cpp = cpp

        valid = [PT_HELLO, PT_CAPS_RESPONSE]
        if not cpp.is_online() and msg_type not in valid:
            LOG.info("CPP %s not ready", addr)
            return

        handler_name = "_handle_%s" % msg_type

        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            handler(msg)

        if msg_type in self.server.pt_types_handlers:
            for handler in self.server.pt_types_handlers[msg_type]:
                handler(msg)

    def send_bye_message_to_self(self):
        """Send bye message to self."""

        msg = {'version': PT_VERSION,
               'type': PT_BYE,
               'seq': self.cpp.seq,
               'cpp': self.cpp.addr,
               'xid': get_xid()}

        self.handle_message(msg)

    def _handle_bye(self, _):
        """Handle bye message."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.cpp_down(self.cpp)

    def send_register_message_to_self(self):
        """Send register message to self."""

        msg = {'version': PT_VERSION,
               'type': PT_REGISTER,
               'seq': self.cpp.seq,
               'cpp': self.cpp.addr,
               'xid': get_xid()}

        self.handle_message(msg)

    def _handle_register(self, _):
        """Handle register message."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.cpp_up(self.cpp)

    def on_close(self):
        """ Handle PNFDev disconnection """

        if not self.cpp:
            return

        LOG.info("CPP disconnected: %s", self.cpp.addr)

        # remove hosted lvnfs
        for tenant in RUNTIME.tenants.values():
            for lvnf in list(tenant.lvnfs.values()):
                if lvnf.cpp == self.cpp:
                    lvnf.cpp = None

        # reset state
        self.cpp.set_disconnected()
        self.cpp.last_seen = 0
        self.cpp.connection = None
        self.cpp.supports = set()
        self.cpp.datapath = None
        self.cpp = None

    def send_message(self, message_type, message):
        """Add fixed header fields and send message. """

        message['version'] = PT_VERSION
        message['type'] = message_type
        message['seq'] = self.cpp.seq
        message['xid'] = get_xid()

        LOG.info("Sending %s seq %u xid %u",
                 message['type'],
                 message['seq'],
                 message['xid'])

        self.write_message(json.dumps(message, cls=EmpowerEncoder))

        return message['xid']

    def send_lvnf_status_request(self):
        """Send del LVNF."""

        msg = {}
        self.send_message(PT_LVNF_STATUS_REQUEST, msg)

    def send_caps_request(self):
        """Send del LVNF."""

        msg = {}
        self.send_message(PT_CAPS_REQUEST, msg)

    def send_del_lvnf(self, lvnf_id):
        """Send del LVNF."""

        undeploy = {'lvnf_id': lvnf_id}
        return self.send_message(PT_DEL_LVNF, undeploy)

    def send_add_lvnf(self, image, lvnf_id, tenant_id, context=None):
        """Send add LVNF."""

        deploy = {'lvnf_id': lvnf_id,
                  'tenant_id': tenant_id,
                  'image': image.to_dict(),
                  'context': context}

        return self.send_message(PT_ADD_LVNF, deploy)

    def _handle_hello(self, hello):
        """Handle an incoming PNFDEV_HELLO message.

        Args:
            hello, a HELLO message

        Returns:
            None
        """

        # New connection
        if not self.cpp.connection:

            # save remote address
            self.addr = self.request.remote_ip

            # set connection
            self.cpp.connection = self

            # change state
            self.cpp.set_connected()

            # send caps request
            self.send_caps_request()

        # Update PNFDev params
        self.cpp.period = hello['every']
        self.cpp.last_seen = hello['seq']
        self.cpp.last_seen_ts = time.time()

    def _handle_caps_response(self, caps):
        """Handle an incoming cap response message.

        Args:
            caps, a CAP_RESPONSE message

        Returns:
            None
        """

        dpid = DPID(caps['dpid'])

        if dpid not in RUNTIME.datapaths:
            RUNTIME.datapaths[dpid] = Datapath(dpid)

        self.cpp.datapath = RUNTIME.datapaths[dpid]

        for port_id, port in caps['ports'].items():

            if int(port_id) not in self.cpp.datapath.network_ports:

                network_port = NetworkPort(dp=self.cpp.datapath,
                                           port_id=int(port['port_id']),
                                           hwaddr=EtherAddress(port['hwaddr']),
                                           iface=port['iface'])

                self.cpp.datapath.network_ports[int(port_id)] = network_port

        # set state to online
        self.cpp.set_online()

        # fetch active lvnfs
        self.send_lvnf_status_request()

    def _handle_add_lvnf_response(self, response):
        """Handle an incoming ADD_LVNF_RESPONSE message.

        Args:
            response, a ADD_LVNF_RESPONSE message

        Returns:
            None
        """

        if response['returncode'] is not None:

            LOG.error("Unable to start LVNF %s, returncode %u",
                      response['lvnf_id'], response['returncode'])

            tenant_id = uuid.UUID(response['tenant_id'])
            lvnf_id = uuid.UUID(response['lvnf_id'])

            if tenant_id not in RUNTIME.tenants:
                LOG.warning("Tenant %s not found, ignoring LVNF %s", tenant_id,
                            lvnf_id)
                return

            tenant = RUNTIME.tenants[tenant_id]

            if lvnf_id not in tenant.lvnfs:
                LOG.warning("LVNF %s not found, ignoring", lvnf_id)
                return

            del tenant.lvnfs[lvnf_id]

            return

        # update dpid
        dpid = DPID(response['dpid'])

        if dpid not in RUNTIME.datapaths:
            RUNTIME.datapaths[dpid] = Datapath(dpid)

        self.cpp.datapath = RUNTIME.datapaths[dpid]

        # update network ports
        for port in response['ports'].values():

            if port['ovs_port_id'] not in self.cpp.datapath.network_ports:

                network_port = NetworkPort(dp=self.cpp.datapath,
                                           port_id=port['ovs_port_id'],
                                           hwaddr=EtherAddress(port['hwaddr']),
                                           iface=port['iface'])

                self.cpp.datapath.network_ports[port['ovs_port_id']] = \
                    network_port

        # update lvnf
        tenant_id = uuid.UUID(response['tenant_id'])
        lvnf_id = uuid.UUID(response['lvnf_id'])

        if tenant_id not in RUNTIME.tenants:
            LOG.warning("Tenant %s not found, ignoring LVNF %s", tenant_id,
                        lvnf_id)
            return

        tenant = RUNTIME.tenants[tenant_id]

        if lvnf_id not in tenant.lvnfs:
            LOG.warning("LVNF %s not found, ignoring", lvnf_id)
            return

        lvnf = tenant.lvnfs[lvnf_id]

        lvnf.handle_add_lvnf_response(response['xid'])

        # update virtual ports
        for port in response['ports'].values():

            network_port = self.cpp.datapath.network_ports[port['ovs_port_id']]
            virtual_port_id = port['virtual_port_id']

            virtual_port = VirtualPort(endpoint=lvnf,
                                       network_port=network_port,
                                       virtual_port_id=virtual_port_id)

            lvnf.ports[virtual_port.virtual_port_id] = virtual_port

    def _handle_del_lvnf_response(self, response):
        """Handle an incoming del_LVNF_RESPONSE message.

        Args:
            response, a del_LVNF_RESPONSE message

        Returns:
            None
        """

        # update lvnf
        tenant_id = uuid.UUID(response['tenant_id'])
        lvnf_id = uuid.UUID(response['lvnf_id'])

        if tenant_id not in RUNTIME.tenants:
            LOG.warning("Tenant %s not found, ignoring LVNF %s", tenant_id,
                        lvnf_id)
            return

        tenant = RUNTIME.tenants[tenant_id]

        if lvnf_id not in tenant.lvnfs:
            LOG.warning("LVNF %s not found, ignoring", lvnf_id)
            return

        lvnf = tenant.lvnfs[lvnf_id]

        lvnf.handle_del_lvnf_response(response['xid'], response['context'])

        # remove virtual ports
        lvnf.ports.clear()

        if not lvnf.target_cpp:
            del tenant.lvnfs[lvnf_id]

    def _handle_lvnf_status_response(self, response):
        """Handle an incoming LVNF_STATUS_RESPONSE message.

        Args:
            status_lvnf, a LVNF_STATUS_RESPONSE message

        Returns:
            None
        """

        # update dpid
        dpid = DPID(response['dpid'])

        if dpid not in RUNTIME.datapaths:
            RUNTIME.datapaths[dpid] = Datapath(dpid)

        self.cpp.datapath = RUNTIME.datapaths[dpid]

        # update network ports
        for port in response['ports'].values():

            if port['ovs_port_id'] not in self.cpp.datapath.network_ports:

                network_port = NetworkPort(dp=self.cpp.datapath,
                                           port_id=port['ovs_port_id'],
                                           hwaddr=EtherAddress(port['hwaddr']),
                                           iface=port['iface'])

                self.cpp.datapath.network_ports[port['ovs_port_id']] = \
                    network_port

        # update lvnf
        tenant_id = uuid.UUID(response['tenant_id'])
        lvnf_id = uuid.UUID(response['lvnf_id'])

        if tenant_id not in RUNTIME.tenants:
            LOG.warning("Tenant %s not found, ignoring LVNF %s", tenant_id,
                        lvnf_id)
            return

        tenant = RUNTIME.tenants[tenant_id]

        # Add lvnf to tenant if not present
        if lvnf_id not in tenant.lvnfs:

            LOG.warning("LVNF %s not found, adding.", lvnf_id)

            img_dict = response['image']

            image = Image(nb_ports=img_dict['nb_ports'],
                          vnf=img_dict['vnf'],
                          state_handlers=img_dict['state_handlers'],
                          handlers=img_dict['handlers'])

            tenant.lvnfs[lvnf_id] = LVNF(lvnf_id,
                                         tenant,
                                         image,
                                         PROCESS_RUNNING)

            tenant.lvnfs[lvnf_id]._cpp = self.cpp
            tenant.lvnfs[lvnf_id].datapath = self.cpp.datapath

        lvnf = tenant.lvnfs[lvnf_id]

        # update virtual ports
        for port in response['ports'].values():

            network_port = self.cpp.datapath.network_ports[port['ovs_port_id']]
            virtual_port_id = port['virtual_port_id']

            virtual_port = VirtualPort(endpoint=lvnf,
                                       network_port=network_port,
                                       virtual_port_id=virtual_port_id)

            lvnf.ports[virtual_port.virtual_port_id] = virtual_port

        LOG.info("LVNF Status: %s", lvnf)
