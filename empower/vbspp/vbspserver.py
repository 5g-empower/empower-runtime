#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio, Supreeth Herle
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

"""VBSP Server."""

from protobuf_to_dict import protobuf_to_dict
from tornado.tcpserver import TCPServer

from empower.core.pnfpserver import BaseTenantPNFDevHandler
from empower.core.pnfpserver import BasePNFDevHandler
from empower.restserver.restserver import RESTServer
from empower.core.pnfpserver import PNFPServer
from empower.persistence.persistence import TblVBSP
from empower.core.vbsp import VBSP
from empower.vbspp import PRT_TYPES
from empower.vbspp import PRT_TYPES_HANDLERS
from empower.vbspp.vbspconnection import VBSPConnection
from empower.vbspp import DEFAULT_PORT
from empower.core.module import ModuleEventWorker
from empower.core.module import ModuleWorker

from empower.main import RUNTIME


class TenantVBSPHandler(BaseTenantPNFDevHandler):
    """TenantVBSP Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbsps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbsps/([a-zA-Z0-9:]*)/?"]


class VBSPHandler(BasePNFDevHandler):
    """VBSP Handler."""

    HANDLERS = [(r"/api/v1/vbsps/?"),
                (r"/api/v1/vbsps/([a-zA-Z0-9:]*)/?")]


class ModuleVBSPPEventWorker(ModuleEventWorker):
    """Module worker (VBSP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleEventWorker.__init__(self, VBSPServer.__module__, module,
                                   pt_type, pt_packet)


class ModuleVBSPPWorker(ModuleWorker):
    """Module worker (VBSP Protocol Server version).
    Keeps track of the currently defined modules for each tenant (events only)
    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleWorker.__init__(self, VBSPServer.__module__, module, pt_type,
                              pt_packet)

    def handle_packet(self, response):
        """Handle response message."""

        msg_type = response.WhichOneof("msg")
        dict_form_msg = protobuf_to_dict(response)
        id_module = dict_form_msg[msg_type]["header"]["xid"]

        if id_module not in self.modules:
            return

        module = self.modules[id_module]

        self.log.info("Received %s response (id=%u)", self.module.MODULE_NAME,
                      response.module_id)

        module.handle_response(response)


class VBSPServer(PNFPServer, TCPServer):
    """Exposes the VBSP API."""

    PNFDEV = VBSP
    TBL_PNFDEV = TblVBSP

    def __init__(self, port, prt_types, prt_types_handlers):

        PNFPServer.__init__(self, prt_types, prt_types_handlers)
        TCPServer.__init__(self)

        self.port = int(port)
        self.connection = None

        self.listen(self.port)

    def handle_stream(self, stream, address):
        self.log.info('Incoming connection from %r', address)
        self.connection = VBSPConnection(stream, address, server=self)


def launch(port=DEFAULT_PORT):
    """Start VBSP Server Module."""

    server = VBSPServer(port, PRT_TYPES, PRT_TYPES_HANDLERS)

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(TenantVBSPHandler, server)
    rest_server.add_handler_class(VBSPHandler, server)

    server.log.info("VBSP Server available at %u", server.port)
    return server
