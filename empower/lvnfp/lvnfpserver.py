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

import tornado.web
import tornado.ioloop
import tornado.websocket

from empower.core.pnfpserver import PNFPServer
from empower.core.restserver import RESTServer
from empower.core.pnfpserver import BaseTenantPNFDevHandler
from empower.core.pnfpserver import BasePNFDevHandler
from empower.persistence.persistence import TblCPP
from empower.scylla.lvnfp import PT_TYPES
from empower.scylla.lvnfp import PT_TYPES_HANDLERS
from empower.scylla.lvnfp.lvnfpmainhandler import LVNFPMainHandler
from empower.scylla.lvnfp.tenantlvnfhandler import TenantLVNFHandler
from empower.scylla.lvnfp.tenantlvnfporthandler import TenantLVNFPortHandler
from empower.scylla.lvnfp.tenantlvnfnexthandler import TenantLVNFNextHandler
from empower.scylla.cpp import CPP

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

DEFAULT_PORT = 4422


class TenantCPPHandler(BaseTenantPNFDevHandler):
    """TenantCPPHandler Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/cpps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/cpps/([a-zA-Z0-9:]*)/?"]


class CPPHandler(BasePNFDevHandler):
    """CPP Handler."""

    HANDLERS = [(r"/api/v1/cpps/?"),
                (r"/api/v1/cpps/([a-zA-Z0-9:]*)/?")]


class LVNFPServer(PNFPServer, tornado.web.Application):
    """Exposes the Scylla LVNF API."""

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

    LOG.info("LVNF Server available at %u", server.port)
    return server
