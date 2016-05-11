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

"""LVAP Protocol Server."""

from tornado.tcpserver import TCPServer

from empower.core.pnfpserver import BaseTenantPNFDevHandler
from empower.core.pnfpserver import BasePNFDevHandler
from empower.restserver.restserver import RESTServer
from empower.core.pnfpserver import PNFPServer
from empower.lvapp.lvappconnection import LVAPPConnection
from empower.persistence.persistence import TblWTP
from empower.core.wtp import WTP

from empower.lvapp import PT_TYPES
from empower.lvapp import PT_TYPES_HANDLERS
from empower.lvapp.lvaphandler import LVAPHandler
from empower.lvapp.tenantlvaphandler import TenantLVAPHandler
from empower.lvapp.tenantvaphandler import TenantVAPHandler
from empower.lvapp.tenantlvapporthandler import TenantLVAPPortHandler
from empower.lvapp.tenantlvapnexthandler import TenantLVAPNextHandler

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

DEFAULT_PORT = 4433


class TenantWTPHandler(BaseTenantPNFDevHandler):
    """TenantWTPHandler Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/wtps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/wtps/([a-zA-Z0-9:]*)/?"]


class WTPHandler(BasePNFDevHandler):
    """WTP Handler."""

    HANDLERS = [(r"/api/v1/wtps/?"),
                (r"/api/v1/wtps/([a-zA-Z0-9:]*)/?")]


class LVAPPServer(PNFPServer, TCPServer):
    """Exposes the LVAP API."""

    PNFDEV = WTP
    TBL_PNFDEV = TblWTP

    def __init__(self, port, pt_types, pt_types_handlers):

        PNFPServer.__init__(self, pt_types, pt_types_handlers)
        TCPServer.__init__(self)

        self.port = int(port)
        self.connection = None

        self.listen(self.port)

        self.lvaps = {}
        self.__assoc_id = 0

    def handle_stream(self, stream, address):
        LOG.info('Incoming connection from %r', address)
        self.connection = LVAPPConnection(stream, address, server=self)

    @property
    def assoc_id(self):
        """ Return next association id. """

        self.__assoc_id += 1
        return self.__assoc_id


def launch(port=DEFAULT_PORT):
    """Start LVAPP Server Module."""

    server = LVAPPServer(int(port), PT_TYPES, PT_TYPES_HANDLERS)

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(TenantWTPHandler, server)
    rest_server.add_handler_class(WTPHandler, server)
    rest_server.add_handler_class(LVAPHandler, server)
    rest_server.add_handler_class(TenantLVAPHandler, server)
    rest_server.add_handler_class(TenantVAPHandler, server)
    rest_server.add_handler_class(TenantLVAPPortHandler, server)
    rest_server.add_handler_class(TenantLVAPNextHandler, server)

    LOG.info("LVAP Server available at %u", server.port)
    return server
