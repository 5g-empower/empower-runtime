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
from empower.lvnfp import PT_LVNF_JOIN
from empower.lvnfp import PT_LVNF_LEAVE
from empower.core.networkport import NetworkPort
from empower.core.virtualport import VirtualPort
from empower.core.datapath import Datapath
from empower.core.lvnf import PROCESS_RUNNING
from empower.core.lvnf import PROCESS_SPAWNING
from empower.core.lvnf import PROCESS_STOPPING
from empower.core.lvnf import PROCESS_MIGRATING_STOP
from empower.core.lvnf import PROCESS_MIGRATING_START
from empower.core.lvnf import PROCESS_STOPPED
from empower.lvnfp import PT_BYE
from empower.lvnfp import PT_REGISTER
from empower.lvnfp import PT_VERSION
from empower.core.lvnf import LVNF
from empower.core.image import Image

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

        addr = EtherAddress(msg['addr'])

        if addr not in self.server.pnfdevs:
            LOG.info("Unknown origin %s, closing connection", addr)
            self.close()
            return

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

        if msg['type'] in self.server.pt_types_handlers:
            for handler in self.server.pt_types_handlers[msg['type']]:
                handler(msg)

    def send_bye_message_to_self(self):
        """Send bye message to self."""

        msg = {'version': PT_VERSION,
               'type': PT_BYE,
               'seq': self.cpp.seq,
               'addr': self.cpp.addr}

        self.handle_message(msg)

    def send_register_message_to_self(self):
        """Send register message to self."""

        msg = {'version': PT_VERSION,
               'type': PT_REGISTER,
               'seq': self.cpp.seq,
               'addr': self.cpp.addr}

        self.handle_message(msg)

    def on_close(self):
        """ Handle PNFDev disconnection """

        if not self.cpp:
            return

        # remove hosted lvnfs
        for tenant in RUNTIME.tenants.values():
            for lvnf_id in list(tenant.lvnfs.keys()):
                lvnf = tenant.lvnfs[lvnf_id]
                LOG.info("LVNF LEAVE %s", lvnf.lvnf_id)
                for handler in self.server.pt_types_handlers[PT_LVNF_LEAVE]:
                    handler(lvnf)
                LOG.info("Deleting LVNF: %s", lvnf.lvnf_id)
                tenant = RUNTIME.tenants[lvnf.tenant_id]
                del tenant.lvnfs[lvnf.lvnf_id]

        # reset state
        self.cpp.set_disconnected()
        self.cpp.connection = None
        self.cpp.datapath = None

    def send_message(self, message_type, message):
        """Add fixed header fields and send message. """

        message['version'] = PT_VERSION
        message['type'] = message_type
        message['seq'] = self.cpp.seq

        LOG.info("Sending %s seq %u", message['type'], message['seq'])
        self.write_message(json.dumps(message, cls=EmpowerEncoder))

    def _handle_hello(self, hello):
        """Handle an incoming PNFDEV_HELLO message.

        Args:
            hello, a HELLO message

        Returns:
            None
        """

        cpp_addr = EtherAddress(hello['addr'])

        try:
            cpp = RUNTIME.cpps[cpp_addr]
        except KeyError:
            LOG.info("Hello from unknown CPP (%s)", cpp_addr)
            raise KeyError("Hello from unknown CPP (%s)", cpp_addr)

        # New connection
        if not cpp.connection:

            # save remote address
            self.addr = self.request.remote_ip

            # set pointer to pnfdev object
            self.cpp = cpp

            # set connection
            cpp.connection = self

            # change state
            cpp.set_connected()

        LOG.info("Hello from %s CPP %s seq %u", self.addr, cpp.addr,
                 hello['seq'])

        # Update PNFDev params
        cpp.period = hello['every']
        cpp.last_seen = hello['seq']
        cpp.last_seen_ts = time.time()

    def _handle_caps(self, caps):
        """Handle an incoming cap response message.

        Args:
            caps, a CAP_RESPONSE message

        Returns:
            None
        """

        cpp_addr = EtherAddress(caps['addr'])

        try:
            cpp = RUNTIME.cpps[cpp_addr]
        except KeyError:
            LOG.info("Caps from unknown CPP (%s)", cpp_addr)
            raise KeyError("Hello from unknown CPP (%s)", cpp_addr)

        if 'dpid' not in caps:
            LOG.info("Empty caps from CPP (%s)", cpp_addr)
            # set state to online
            cpp.set_online()
            return

        cpp_dpid = DPID(caps['dpid'])

        if cpp_dpid not in RUNTIME.datapaths:
            RUNTIME.datapaths[cpp_dpid] = Datapath(cpp_dpid)

        cpp.datapath = RUNTIME.datapaths[cpp_dpid]

        for port_id, port in caps['ports'].items():

            if int(port_id) not in cpp.datapath.network_ports:

                network_port = NetworkPort(dp=cpp.datapath,
                                           port_id=int(port['port_id']),
                                           hwaddr=EtherAddress(port['hwaddr']),
                                           iface=port['iface'])

                cpp.datapath.network_ports[int(port_id)] = network_port

        # set state to online
        cpp.set_online()

    def send_del_lvnf(self, lvnf_id):
        """Send del LVNF."""

        undeploy = {'lvnf_id': lvnf_id}
        self.send_message(PT_DEL_LVNF, undeploy)

    def send_add_lvnf(self, image, lvnf_id, tenant_id, context=None):
        """Send add LVNF."""

        deploy = {'lvnf_id': lvnf_id,
                  'tenant_id': tenant_id,
                  'image': image.to_dict(),
                  'context': context}

        self.send_message(PT_ADD_LVNF, deploy)

    def _handle_status_lvnf(self, status_lvnf):
        """Handle an incoming STATUS_LVNF message.

        Args:
            status_lvnf, a STATUS_LVNF message

        Returns:
            None
        """

        addr = EtherAddress(status_lvnf['addr'])
        cpp = RUNTIME.cpps[addr]

        tenant_id = uuid.UUID(status_lvnf['tenant_id'])
        lvnf_id = uuid.UUID(status_lvnf['lvnf_id'])

        if tenant_id not in RUNTIME.tenants:
            LOG.warning("Tenant %s not found, ignoring LVNF %s", tenant_id,
                        lvnf_id)
            return

        tenant = RUNTIME.tenants[tenant_id]

        LOG.info("LVNF %s status update", lvnf_id)

        # Add lvnf to tenant if not present
        if lvnf_id not in tenant.lvnfs:

            LOG.warning("LVNF %s not found, adding.", lvnf_id)

            img_dict = status_lvnf['image']

            image = Image(nb_ports=img_dict['nb_ports'],
                          vnf=img_dict['vnf'],
                          state_handlers=img_dict['state_handlers'],
                          handlers=img_dict['handlers'])

            tenant.lvnfs[lvnf_id] = LVNF(lvnf_id, tenant_id, image, cpp)

        lvnf = tenant.lvnfs[lvnf_id]

        if lvnf.state in (None, PROCESS_RUNNING, PROCESS_SPAWNING,
                          PROCESS_MIGRATING_START):

            if status_lvnf['returncode']:

                # Raise LVNF leave event
                if lvnf.state:
                    LOG.info("LVNF LEAVE %s", lvnf_id)
                    handlers = self.server.pt_types_handlers[PT_LVNF_LEAVE]
                    for handler in handlers:
                        handler(lvnf)

                lvnf.returncode = status_lvnf['returncode']
                lvnf.contex = status_lvnf['context']

                lvnf.state = PROCESS_STOPPED

                return

            # Configure ports

            dp = RUNTIME.datapaths[cpp.datapath.dpid]

            for port in status_lvnf['ports'].values():

                virtual_port_id = port['virtual_port_id']

                if port['hwaddr']:
                    hwaddr = EtherAddress(port['hwaddr'])
                else:
                    hwaddr = None

                if port['ovs_port_id']:
                    port_id = int(port['ovs_port_id'])
                else:
                    port_id = None

                iface = port['iface']

                # caps may bring vnf network ports, create new network port
                # only if it has not been added already
                if port_id not in dp.network_ports:
                    network_port = NetworkPort(dp=dp,
                                               port_id=port_id,
                                               hwaddr=EtherAddress(hwaddr),
                                               iface=iface)

                    dp.network_ports[port_id] = network_port

                network_port = dp.network_ports[port_id]

                virtual_port = VirtualPort(lvnf,
                                           network_port,
                                           virtual_port_id=virtual_port_id)

                lvnf.ports[virtual_port.virtual_port_id] = virtual_port

            lvnf.returncode = status_lvnf['returncode']
            lvnf.contex = status_lvnf['context']

            lvnf.state = PROCESS_RUNNING

            # Raise LVNF join event
            if lvnf.state == PROCESS_RUNNING:
                LOG.info("LVNF JOIN %s", lvnf.lvnf_id)
                handlers = self.server.pt_types_handlers[PT_LVNF_JOIN]
                for handler in handlers:
                    handler(lvnf)

        elif lvnf.state == PROCESS_STOPPING:

            if status_lvnf['returncode']:

                # Raise LVNF leave event
                if lvnf.state:
                    LOG.info("LVNF LEAVE %s", lvnf_id)
                    handlers = self.server.pt_types_handlers[PT_LVNF_LEAVE]
                    for handler in handlers:
                        handler(lvnf)

                lvnf.returncode = status_lvnf['returncode']
                lvnf.contex = status_lvnf['context']

                lvnf.state = PROCESS_STOPPED

                # remove lvnf
                del tenant.lvnfs[lvnf_id]

                return

            IOError("No return code on stopping LVNF")

        elif lvnf.state == PROCESS_MIGRATING_STOP:

            if status_lvnf['returncode']:

                lvnf.returncode = status_lvnf['returncode']
                lvnf.context = status_lvnf['context']

                lvnf.state = PROCESS_MIGRATING_START

                return

            IOError("No returncode on migrating LVNF")

        else:

            raise IOError("Invalid transistion")
