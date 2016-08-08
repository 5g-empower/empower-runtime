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
from empower.core.module import ModuleEventWorker
from empower.persistence.persistence import TblCPP
from empower.lvnfp import PT_TYPES
from empower.lvnfp import PT_TYPES_HANDLERS
from empower.lvnfp.lvnfpmainhandler import LVNFPMainHandler
from empower.lvnfp.tenantlvnfhandler import TenantLVNFHandler
from empower.lvnfp.tenantlvnfporthandler import TenantLVNFPortHandler
from empower.lvnfp.tenantlvnfnexthandler import TenantLVNFNextHandler
from empower.core.cpp import CPP

from empower.main import RUNTIME

DEFAULT_PORT = 4422


class TenantCPPHandler(BaseTenantPNFDevHandler):
    """TenantCPPHandler Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/cpps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/cpps/([a-zA-Z0-9:]*)/?"]


class CPPHandler(BasePNFDevHandler):
    """CPP Handler."""

    HANDLERS = [(r"/api/v1/cpps/?"),
                (r"/api/v1/cpps/([a-zA-Z0-9:]*)/?")]


class ModuleLVNFPWorker(ModuleWorker):
    """Module worker (LVAP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleWorker.__init__(self, LVNFPServer.__module__, module, pt_type,
                              pt_packet)

    def handle_packet(self, response):
        """Handle response message."""

        if response['module_id'] not in self.modules:
            return

        module = self.modules[response['module_id']]

        self.log.info("Received %s response (id=%u)", self.module.MODULE_NAME,
                      response['module_id'])

        module.handle_response(response)


class ModuleLVNFPEventWorker(ModuleEventWorker):
    """Module worker (LVAP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleEventWorker.__init__(self, LVNFPServer.__module__, module,
                                   pt_type, pt_packet)


class LVNFPServer(PNFPServer, tornado.web.Application):
    """Exposes the EmPOWER LVNF API."""

    handlers = [LVNFPMainHandler]

    PNFDEV = CPP
    TBL_PNFDEV = TblCPP

    def __init__(self, port, pt_types, pt_types_handlers):

        PNFPServer.__init__(self, pt_types, pt_types_handlers)

        self.port = int(port)

        handlers = []

        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler, dict(server=self)))

        tornado.web.Application.__init__(self, handlers)
        http_server = tornado.httpserver.HTTPServer(self)
        http_server.listen(self.port)


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
