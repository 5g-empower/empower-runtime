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

"""VBSP Server."""

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

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class TenantVBSPHandler(BaseTenantPNFDevHandler):
    """TenantVBSP Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbsps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbsps/([a-zA-Z0-9:]*)/?"]


class VBSPHandler(BasePNFDevHandler):
    """VBSP Handler."""

    HANDLERS = [(r"/api/v1/vbsps/?"),
                (r"/api/v1/vbsps/([a-zA-Z0-9:]*)/?")]


class VBSPServer(PNFPServer, TCPServer):
    """Exposes the VBSP API."""

    PNFDEV = VBSP
    TBL_PNFDEV = TblVBSP

    def __init__(self, port, prt_types, prt_types_handlers):

        PNFPServer.__init__(self, prt_types, prt_types_handlers)
        TCPServer.__init__(self)

        self.port = int(port)
        self.ues = {}
        self.connection = None

        self.listen(self.port)

    def handle_stream(self, stream, address):
        LOG.info('Incoming connection from %r and %r', address, stream)
        self.connection = VBSPConnection(stream, address, server=self)


def launch(port=DEFAULT_PORT):
    """Start VBSP Server Module."""

    server = VBSPServer(port, PRT_TYPES, PRT_TYPES_HANDLERS)

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(TenantVBSPHandler, server)
    rest_server.add_handler_class(VBSPHandler, server)

    LOG.info("VBSP Server available at %u", server.port)
    return server
