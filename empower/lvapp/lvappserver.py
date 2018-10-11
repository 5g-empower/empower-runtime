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

"""LVAP Protocol Server."""

from tornado.tcpserver import TCPServer

from empower.core.pnfpserver import BaseTenantPNFDevHandler
from empower.core.pnfpserver import BasePNFDevHandler
from empower.restserver.restserver import RESTServer
from empower.core.pnfpserver import PNFPServer
from empower.core.module import ModuleWorker
from empower.lvapp.lvappconnection import LVAPPConnection
from empower.persistence.persistence import TblWTP
from empower.core.wtp import WTP

from empower.lvapp import PT_LVAP_LEAVE
from empower.lvapp import PT_LVAP_JOIN
from empower.lvapp import PT_LVAP_HANDOVER
from empower.lvapp import PT_TYPES
from empower.lvapp import PT_TYPES_HANDLERS
from empower.lvapp.lvaphandler import LVAPHandler
from empower.lvapp.tenantlvaphandler import TenantLVAPHandler

from empower.main import RUNTIME

DEFAULT_PORT = 4433


class TenantWTPHandler(BaseTenantPNFDevHandler):
    """TenantWTPHandler Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/wtps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/wtps/([a-zA-Z0-9:]*)/?"]


class WTPHandler(BasePNFDevHandler):
    """WTP Handler."""

    HANDLERS = [(r"/api/v1/wtps/?"),
                (r"/api/v1/wtps/([a-zA-Z0-9:]*)/?")]


class ModuleLVAPPWorker(ModuleWorker):
    """Module worker (LVAP Server version)."""

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleWorker.__init__(self, LVAPPServer.__module__, module, pt_type,
                              pt_packet)

    def handle_packet(self, pnfdev, message):
        """Handle response message."""

        if message.module_id not in self.modules:
            return

        module = self.modules[message.module_id]

        self.log.info("Received %s response (id=%u) from %s",
                      self.module.MODULE_NAME, message.module_id, pnfdev.addr)

        module.handle_response(message)


class LVAPPServer(PNFPServer, TCPServer):
    """Exposes the LVAP API."""

    PNFDEV = WTP
    TBL_PNFDEV = TblWTP

    def __init__(self, port, pt_types, pt_types_handlers):

        PNFPServer.__init__(self, port, pt_types, pt_types_handlers)
        TCPServer.__init__(self)

        self.connection = None

        self.listen(self.port)

    def handle_stream(self, stream, address):
        self.log.info('Incoming connection from %r', address)
        self.connection = LVAPPConnection(stream, address, server=self)


    def send_lvap_leave_message_to_self(self, lvap):
        """Send an LVAP_LEAVE message to self."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.lvap_leave(lvap)

        for handler in self.pt_types_handlers[PT_LVAP_LEAVE]:
            handler(lvap)

    def send_lvap_join_message_to_self(self, lvap):
        """Send an LVAP_JOIN message to self."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.lvap_join(lvap)

        for handler in self.pt_types_handlers[PT_LVAP_JOIN]:
            handler(lvap)

    def send_lvap_handover_message_to_self(self, lvap, source_blocks):
        """Send an LVAP_HANDOVER message to self."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.lvap_handover(lvap, source_blocks)

        for handler in self.pt_types_handlers[PT_LVAP_HANDOVER]:
            handler(lvap, source_blocks)


def launch(port=DEFAULT_PORT):
    """Start LVAPP Server Module."""

    server = LVAPPServer(int(port), PT_TYPES, PT_TYPES_HANDLERS)

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(TenantWTPHandler, server)
    rest_server.add_handler_class(WTPHandler, server)
    rest_server.add_handler_class(LVAPHandler, server)
    rest_server.add_handler_class(TenantLVAPHandler, server)

    server.log.info("LVAP Server available at %u", server.port)
    return server
