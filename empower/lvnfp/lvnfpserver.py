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

import tornado.web
import tornado.ioloop
import tornado.websocket

from empower.core.pnfpserver import PNFPServer
from empower.restserver.restserver import RESTServer
from empower.core.pnfpserver import BaseTenantPNFDevHandler
from empower.core.pnfpserver import BasePNFDevHandler
from empower.core.module import ModuleWorker
from empower.persistence.persistence import TblCPP
from empower.lvnfp import PT_BYE
from empower.lvnfp import PT_TYPES
from empower.lvnfp import PT_LVNF_LEAVE
from empower.lvnfp import PT_LVNF_JOIN
from empower.lvnfp import PT_TYPES_HANDLERS
from empower.lvnfp.lvnfpmainhandler import LVNFPMainHandler
from empower.lvnfp.tenantlvnfhandler import TenantLVNFHandler
from empower.lvnfp.tenantlvnfporthandler import TenantLVNFPortHandler
from empower.lvnfp.tenantlvnfnexthandler import TenantLVNFNextHandler
from empower.core.cpp import CPP

from empower.main import RUNTIME

DEFAULT_PORT = 4422


class TenantCPPHandler(BaseTenantPNFDevHandler):
    """TenantCPPHandler Handler.

    Used to view and manipulate CPPs. This handler has access to the Tenant CPPs Notice how a CPP is a subclass of PNFDev.
    """

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/cpps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/cpps/([a-zA-Z0-9:]*)/?"]


class CPPHandler(BasePNFDevHandler):
    """CPP Handler. Used to view and manipulate CPPs.

    Used to view and manipulate CPPs. This handler has access to the system wide CPPs Notice how a CPP is a subclass of PNFDev."""

    HANDLERS = [(r"/api/v1/cpps/?"),
                (r"/api/v1/cpps/([a-zA-Z0-9:]*)/?")]


class ModuleLVNFPWorker(ModuleWorker):
    """Module worker (LVNF Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleWorker.__init__(self, LVNFPServer.__module__, module, pt_type,
                              pt_packet)

    def handle_packet(self, msg):
        """Handle response message."""

        if msg['module_id'] not in self.modules:
            return

        module = self.modules[msg['module_id']]

        self.log.info("Received %s response (id=%u)", self.module.MODULE_NAME,
                      msg['module_id'])

        module.handle_response(msg)


class LVNFPServer(PNFPServer, tornado.web.Application):
    """Exposes the EmPOWER LVNF API."""

    handlers = [LVNFPMainHandler]

    PNFDEV = CPP
    TBL_PNFDEV = TblCPP

    def __init__(self, port, pt_types, pt_types_handlers):

        PNFPServer.__init__(self, port, pt_types, pt_types_handlers)

        handlers = []

        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler, dict(server=self)))

        tornado.web.Application.__init__(self, handlers)
        http_server = tornado.httpserver.HTTPServer(self)
        http_server.listen(self.port)

    def send_lvnf_leave_message_to_self(self, lvnf):
        """Send an LVNF_LEAVE message to self."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.lvnf_leave(lvnf)

        for handler in self.pt_types_handlers[PT_LVNF_LEAVE]:
            handler(lvnf)

    def send_lvnf_join_message_to_self(self, lvnf):
        """Send an LVNF_JOIN message to self."""

        for tenant in RUNTIME.tenants.values():
            for app in tenant.components.values():
                app.lvnf_join(lvnf)

        for handler in self.pt_types_handlers[PT_LVNF_JOIN]:
            handler(lvnf)


def launch(port=DEFAULT_PORT):
    """Start LVNFP Server Module. """

    server = LVNFPServer(int(port), PT_TYPES, PT_TYPES_HANDLERS)

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(TenantCPPHandler, server)
    rest_server.add_handler_class(CPPHandler, server)
    rest_server.add_handler_class(TenantLVNFHandler, server)
    rest_server.add_handler_class(TenantLVNFPortHandler, server)
    rest_server.add_handler_class(TenantLVNFNextHandler, server)

    server.log.info("LVNF Server available at %u", server.port)
    return server
