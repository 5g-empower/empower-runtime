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

"""LVNFP Protocol Server."""

import uuid
import time
import json
import tornado.web
import tornado.ioloop
import tornado.websocket

from empower.core.networkport import NetworkPort
from empower.datatypes.etheraddress import EtherAddress
from empower.core.jsonserializer import EmpowerEncoder
from empower.lvnfp import PT_ADD_LVNF
from empower.lvnfp import PT_DEL_LVNF
from empower.lvnfp import PT_LVNF_JOIN
from empower.lvnfp import PT_LVNF_LEAVE
from empower.lvnfp import PT_BYE
from empower.lvnfp import PT_REGISTER
from empower.lvnfp import PT_VERSION
from empower.lvnfp import PT_CAPS_REQUEST
from empower.core.lvnf import LVNF
from empower.core.virtualport import VirtualPortLvnf
from empower.core.lvnf import PROCESS_RUNNING
from empower.core.lvnf import PROCESS_STOPPED
from empower.core.lvnf import PROCESS_DONE
from empower.core.lvnf import PROCESS_M1
from empower.core.lvnf import PROCESS_M2
from empower.core.lvnf import PROCESS_M3
from empower.core.image import Image

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class LVNFPMainHandler(tornado.websocket.WebSocketHandler):

    HANDLERS = [r"/"]

    def initialize(self, server):
        self.pnfdev = None
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
               'seq': self.pnfdev.seq,
               'addr': self.pnfdev.addr}

        self.handle_message(msg)

    def send_register_message_to_self(self):
        """Send register message to self."""

        msg = {'version': PT_VERSION,
               'type': PT_REGISTER,
               'seq': self.pnfdev.seq,
               'addr': self.pnfdev.addr}

        self.handle_message(msg)

    def on_close(self):
        """ Handle PNFDev disconnection """

        if not self.pnfdev:
            return

        # reset state
        self.pnfdev.connection = None
        self.pnfdev.ports = {}

        # remove hosted lvnfs
        to_be_removed = []
        for tenant in RUNTIME.tenants.values():
            for lvnf in tenant.lvnfs.values():
                if lvnf.cpp == self.pnfdev:
                    to_be_removed.append(lvnf)

        for lvnf in to_be_removed:
            LOG.info("LVNF LEAVE %s" % (lvnf.lvnf_id))
            for handler in self.server.pt_types_handlers[PT_LVNF_LEAVE]:
                handler(lvnf)
            LOG.info("Deleting LVNF: %s" % lvnf.lvnf_id)
            tenant = RUNTIME.tenants[lvnf.tenant_id]
            del tenant.lvnfs[lvnf.lvnf_id]

    def send_message(self, message_type, message):
        """Add fixed header fields and send message. """

        message['version'] = PT_VERSION
        message['type'] = message_type
        message['seq'] = self.pnfdev.seq

        LOG.info("Sending %s seq %u" % (message['type'], message['seq']))
        self.write_message(json.dumps(message, cls=EmpowerEncoder))

    def _handle_bye(self, pnfdev_bye):
        """Handle an incoming PNFDEV_BYE message.

        Args:
            hello, a PNFDEV_BYE message

        Returns:
            None
        """

        # reset PNFDev state
        self.pnfdev.last_seen = 0
        self.pnfdev.last_seen_ts = 0
        self.pnfdev.telemetry = {}

    def _handle_hello(self, hello):
        """Handle an incoming PNFDEV_HELLO message.

        Args:
            hello, a HELLO message

        Returns:
            None
        """

        addr = EtherAddress(hello['addr'])
        pnfdev = self.server.pnfdevs[addr]

        # compute delta if not new connection
        if pnfdev.connection:

            delta = time.time() - pnfdev.last_seen_ts

            # downlink
            dl_bytes = hello['downlink_bytes'] - pnfdev.downlink_bytes
            pnfdev.downlink_bit_rate = int(dl_bytes / delta) * 8

            # uplink
            ul_bytes = hello['uplink_bytes'] - pnfdev.uplink_bytes
            pnfdev.uplink_bit_rate = int(ul_bytes / delta) * 8

        # New connection
        if not pnfdev.connection:

            # save remote address
            self.addr = self.request.remote_ip

            # set pointer to pnfdev object
            self.pnfdev = pnfdev

            # set connection (this will trigger a register message)
            pnfdev.connection = self

            # send out caps request
            self.send_caps_requests()

        # Update PNFDev params
        pnfdev.every = hello['every']
        pnfdev.last_seen = hello['seq']
        pnfdev.uplink_bytes = hello['uplink_bytes']
        pnfdev.downlink_bytes = hello['downlink_bytes']

        pnfdev.last_seen_ts = time.time()

    def _handle_caps_response(self, caps):
        """Handle an incoming cap response message.

        Args:
            caps, a CAP_RESPONSE message

        Returns:
            None
        """

        addr = EtherAddress(caps['addr'])
        pnfdev = self.server.pnfdevs[addr]
        pnfdev.ports = {}

        for port in caps['ports'].values():

            network_port = NetworkPort(dpid=pnfdev.addr,
                                       port_id=port['port_id'],
                                       iface=port['iface'],
                                       hwaddr=EtherAddress(port['hwaddr']))

            pnfdev.ports[network_port.port_id] = network_port

    def send_caps_requests(self):
        """Send del CAP request message."""

        caps = {}
        self.send_message(PT_CAPS_REQUEST, caps)

    def _handle_error(self, error):
        """Handle an incoming ERROR message.
        Args:
            error, a ERROR message
        Returns:
            None
        """

        LOG.info("%s message from %s at %s seq %u code %u %s",
                 error['type'], error['addr'], self.request.remote_ip,
                 error['seq'], error['code'], error['message'])

    def send_del_lvnf(self, lvnf_id):
        """Send del LVNF."""

        undeploy = {'lvnf_id': lvnf_id}
        self.send_message(PT_DEL_LVNF, undeploy)

    def send_add_lvnf(self, image, lvnf_id, tenant_id):
        """Send add LVNF."""

        deploy = {'lvnf_id': lvnf_id,
                  'tenant_id': tenant_id,
                  'image': image.to_dict()}

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

        tenant = RUNTIME.tenants[tenant_id]

        LOG.info("LVNF %s status update: %s" %
                 (lvnf_id, status_lvnf['process']))

        # Add lvnf to tenant if not present
        if lvnf_id not in tenant.lvnfs:

            LOG.warning("LVNF %s not found, adding." % lvnf_id)

            img_dict = status_lvnf['image']

            image = Image(nb_ports=img_dict['nb_ports'],
                          vnf=img_dict['vnf'],
                          state_handlers=img_dict['state_handlers'],
                          handlers=img_dict['handlers'])

            tenant.lvnfs[lvnf_id] = LVNF(lvnf_id, tenant_id, image, cpp)

        lvnf = tenant.lvnfs[lvnf_id]

        # Got a LVNF stop message, this could be due to a migration, i.e. the
        # old LVNF being removed or as a response to a del_lvnf message from
        # the controller.
        if status_lvnf['process'] == PROCESS_STOPPED:

            # A migration is undergoing, process stopped message must be
            # ignored otherwise the LVNF state will be lost. Just set lvnf
            # process property so migration can continue
            if lvnf.process == PROCESS_M2:
                lvnf.process = PROCESS_STOPPED
                return

            # this should not happen
            if lvnf.cpp != cpp:
                raise IOError("CPP mismatch")

            # Stop messages must not arrive during migration
            if lvnf.process in [PROCESS_M1, PROCESS_M3]:
                raise IOError("Unknown LVNF")

            # The status update is coming from the CPP where this LVNF was
            # active, then this is the result of LVNF delete command coming
            # from the controller.
            LOG.info("LVNF LEAVE %s" % (lvnf_id))
            for handler in self.server.pt_types_handlers[PT_LVNF_LEAVE]:
                handler(lvnf)

            LOG.info("Removing LVNF %s" % lvnf_id)
            del tenant.lvnfs[lvnf_id]

            return

        # reset ports and returcode/message
        lvnf.ports = {}
        lvnf.returncode = None
        lvnf.message = None

        if status_lvnf['process'] == PROCESS_RUNNING:

            # Raise LVNF join event
            if lvnf.process != PROCESS_RUNNING:
                LOG.info("LVNF JOIN %s" % (lvnf_id))
                for handler in self.server.pt_types_handlers[PT_LVNF_JOIN]:
                    handler(lvnf)

            # Configure ports
            for port in status_lvnf['ports'].values():

                virtual_port_id = port['virtual_port_id']

                if port['hwaddr']:
                    hwaddr = EtherAddress(port['hwaddr'])
                else:
                    hwaddr = None

                if port['ovs_port_id']:
                    ovs_port_id = int(port['ovs_port_id'])
                else:
                    ovs_port_id = None

                virtual_port = VirtualPortLvnf(dpid=lvnf.cpp.addr,
                                               ovs_port_id=ovs_port_id,
                                               virtual_port_id=virtual_port_id,
                                               iface=port['iface'],
                                               hwaddr=hwaddr)

                # these are used by the overridden dict methods
                virtual_port.next.lvnf = lvnf
                virtual_port.next.port = virtual_port

                lvnf.ports[virtual_port.virtual_port_id] = virtual_port

        if status_lvnf['process'] == PROCESS_DONE:

            # Raise LVNF leave event
            if lvnf.process != PROCESS_DONE:
                LOG.info("LVNF LEAVE %s" % (lvnf_id))
                for handler in self.server.pt_types_handlers[PT_LVNF_LEAVE]:
                    handler(lvnf)

            # Set error message
            lvnf.returncode = status_lvnf['returncode']
            lvnf.message = status_lvnf['message']

        # set new process
        lvnf.process = status_lvnf['process']
