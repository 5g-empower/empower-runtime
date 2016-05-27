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

"""Handlers poller module."""

from uuid import UUID

from empower.core.module import ModuleWorker
from empower.core.module import ModuleHandler
from empower.core.module import Module
from empower.core.module import bind_module
from empower.core.module import handle_callback
from empower.handlers import PT_WRITE_HANDLER_REQUEST
from empower.handlers import PT_WRITE_HANDLER_RESPONSE
from empower.lvnfp.lvnfpserver import LVNFPServer
from empower.restserver.restserver import RESTServer

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class WriteHandler(Module):
    """WriteHandler object."""

    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvnf_id', 'handler',
                'value']

    def __init__(self):

        super().__init__()

        self.__lvnf_id = None
        self.__handler = None
        self.value = None
        self.samples = None
        self.retcode = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.lvnf_id == other.lvnf_id and \
            self.handler == other.handler and \
            self.value == other.value

    @property
    def handler(self):
        """Return the handler name."""

        return self.__handler

    @handler.setter
    def handler(self, handler):
        """Set the handler name."""

        tenant = RUNTIME.tenants[self.tenant_id]
        lvnf = tenant.lvnfs[self.lvnf_id]

        if handler not in lvnf.image.handlers:
            raise KeyError("Handler %s not found" % handler)

        self.__handler = handler

    @property
    def lvnf_id(self):
        return self.__lvnf_id

    @lvnf_id.setter
    def lvnf_id(self, value):
        self.__lvnf_id = UUID(str(value))

    def to_dict(self):
        """Return a JSON-serializable representation of this object."""

        out = super().to_dict()

        out['lvnf_id'] = self.lvnf_id
        out['handler'] = self.handler
        out['samples'] = self.samples
        out['retcode'] = self.retcode

        return out

    def run_once(self):
        """Send out handler requests."""

        worker = RUNTIME.components[self.worker.__module__]
        worker.send_write_handler_request(self)


class WriteHandlerHandler(ModuleHandler):
    pass


class WriteHandlerWorker(ModuleWorker):
    """WriteHandler worker."""

    MODULE_NAME = "write_handler"
    MODULE_HANDLER = WriteHandlerHandler
    MODULE_TYPE = WriteHandler

    def send_write_handler_request(self, handler):
        """Send a WRITE_HANDLER_REQUEST message."""

        if handler.tenant_id not in RUNTIME.tenants:
            self.remove_module(handler.module_id)
            return

        tenant = RUNTIME.tenants[handler.tenant_id]

        if handler.lvnf_id not in tenant.lvnfs:
            LOG.error("LVNF %s not found.", handler.lvnf_id)
            self.remove_module(handler.module_id)
            return

        lvnf = tenant.lvnfs[handler.lvnf_id]

        if not lvnf.cpp.connection:
            return

        handler_req = {'handler_id': handler.module_id,
                       'lvnf_id': handler.lvnf_id,
                       'tenant_id': handler.tenant_id,
                       'handler': lvnf.image.handlers[handler.handler],
                       'value': handler.value}

        lvnf.cpp.connection.send_message(PT_WRITE_HANDLER_REQUEST, handler_req)

    def handle_write_handler_response(self, handler_response):
        """Handle an incoming WRITE_HANDLER_RESPONSE message.
        Args:
            handler_response, a WRITE_HANDLER_RESPONSE message
        Returns:
            None
        """

        if handler_response['handler_id'] not in self.modules:
            return

        handler = self.modules[handler_response['handler_id']]

        tenant_id = UUID(handler_response['tenant_id'])
        lvnf_id = UUID(handler_response['lvnf_id'])

        tenant = RUNTIME.tenants[tenant_id]

        if lvnf_id not in tenant.lvnfs:
            return

        # update this object
        if handler_response['retcode'] != 200:
            error = handler_response['samples']
            LOG.error("Error while polling %s: %s" % (handler.handler, error))
            self.remove_module(handler.module_id)
            return

        handler.retcode = handler_response['retcode']
        handler.samples = handler_response['samples']

        # handle callback
        handle_callback(handler, handler)


bind_module(WriteHandlerWorker)


def launch():
    """Initialize the module."""

    lvnf_server = RUNTIME.components[LVNFPServer.__module__]
    rest_server = RUNTIME.components[RESTServer.__module__]

    worker = WriteHandlerWorker(rest_server)
    lvnf_server.register_message(PT_WRITE_HANDLER_RESPONSE,
                                 None,
                                 worker.handle_write_handler_response)

    return worker
