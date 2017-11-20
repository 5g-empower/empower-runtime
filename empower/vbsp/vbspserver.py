#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

from tornado.tcpserver import TCPServer

from empower.core.pnfpserver import BaseTenantPNFDevHandler
from empower.core.pnfpserver import BasePNFDevHandler
from empower.restserver.restserver import RESTServer
from empower.core.pnfpserver import PNFPServer
from empower.core.module import ModuleWorker
from empower.core.module import ModuleEventWorker
from empower.vbsp.vbspconnection import VBSPConnection
from empower.persistence.persistence import TblVBS
from empower.core.vbs import VBS

from empower.vbsp import PT_BYE
from empower.vbsp import PT_UE_LEAVE
from empower.vbsp import PT_UE_JOIN
from empower.vbsp import PT_TYPES
from empower.vbsp import PT_TYPES_HANDLERS
from empower.vbsp.uehandler import UEHandler
from empower.vbsp.tenantuehandler import TenantUEHandler
from empower.vbsp.tenantuehandler import TenantUEHandler

from empower.main import RUNTIME

DEFAULT_PORT = 2210


class TenantVBSHandler(BaseTenantPNFDevHandler):
    """TenantVBS Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbses/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbses/([a-zA-Z0-9:]*)/?"]


class VBSHandler(BasePNFDevHandler):
    """VBS Handler."""

    HANDLERS = [(r"/api/v1/vbses/?"),
                (r"/api/v1/vbses/([a-zA-Z0-9:]*)/?")]


class ModuleVBSPEventWorker(ModuleEventWorker):
    """Module worker (VBSP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):

        ModuleEventWorker.__init__(self, VBSPServer.__module__, module,
                                   pt_type, pt_packet)


class ModuleVBSPWorker(ModuleWorker):
    """Module worker (VBSP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleWorker.__init__(self, VBSPServer.__module__, module, pt_type,
                              pt_packet)

        self.pnfp_server.register_message(PT_BYE, None, self.handle_bye)
        self.pnfp_server.register_message(PT_UE_LEAVE, None, self.
                                          handle_ue_leave)

    def handle_ue_leave(self, ue):
        """UE left."""

        for module_id in list(self.modules.keys()):
            module = self.modules[module_id]
            if hasattr(module, "ue") and module.ue == ue:
                self.modules[module_id].unload()

    def handle_bye(self, vbs):
        """VBS left."""

        for module_id in list(self.modules.keys()):
            module = self.modules[module_id]
            if hasattr(module, "vbs") and module.vbs == vbs:
                self.modules[module_id].unload()

    def handle_packet(self, vbs, hdr, event, msg):
        """Handle response message."""

        if hdr.modid not in self.modules:
            return

        module = self.modules[hdr.modid]

        self.log.info("Received %s response (id=%u, op=%u)",
                      self.module.MODULE_NAME, hdr.modid, event.op)

        if event.op == 1:
            module.handle_response(msg)


class VBSPServer(PNFPServer, TCPServer):
    """Exposes the VBS API."""

    PNFDEV = VBS
    TBL_PNFDEV = TblVBS

    def __init__(self, port, prt_types, prt_types_handlers):

        PNFPServer.__init__(self, port, prt_types, prt_types_handlers)
        TCPServer.__init__(self)

        self.connection = None

        self.listen(self.port)

        self.pending = {}

    def handle_stream(self, stream, address):
        self.log.info('Incoming connection from %r', address)
        self.connection = VBSPConnection(stream, address, server=self)

    def send_ue_leave_message_to_self(self, ue):
        """Send an UE_LEAVE message to self."""

        self.log.info("UE LEAVE %u (%s)", ue.imsi, ue.plmn_id)
        for handler in self.pt_types_handlers[PT_UE_LEAVE]:
            handler(ue)

    def send_ue_join_message_to_self(self, ue):
        """Send an UE_JOIN message to self."""

        self.log.info("UE JOIN %u (%s)", ue.imsi, ue.plmn_id)
        for handler in self.pt_types_handlers[PT_UE_JOIN]:
            handler(ue)


def launch(port=DEFAULT_PORT):
    """Start VBSP Server Module."""

    server = VBSPServer(port, PT_TYPES, PT_TYPES_HANDLERS)

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(TenantVBSHandler, server)
    rest_server.add_handler_class(VBSHandler, server)
    rest_server.add_handler_class(UEHandler, server)
    rest_server.add_handler_class(TenantUEHandler, server)

    server.log.info("VBSP Server available at %u", server.port)
    return server
