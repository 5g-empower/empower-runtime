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

"""LVNF EMS GET command."""

from uuid import UUID

from empower.core.lvnf import LVNF
from empower.core.module import Module
from empower.lvnf_ems import PT_LVNF_GET_REQUEST
from empower.lvnf_ems import PT_LVNF_GET_RESPONSE
from empower.lvnfp.lvnfpserver import ModuleLVNFPWorker

from empower.main import RUNTIME


class LVNFGet(Module):
    """LVNF Get object."""

    MODULE_NAME = "lvnf_get"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvnf', 'handler']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self.__lvnf = None
        self.__handler = None

        # data structures
        self.retcode = None
        self.samples = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.lvnf == other.lvnf and \
            self.handler == other.handler

    @property
    def handler(self):
        """Return the handler name."""

        return self.__handler

    @handler.setter
    def handler(self, handler):
        """Set the handler name."""

        tenant = RUNTIME.tenants[self.tenant_id]
        lvnf = tenant.lvnfs[self.lvnf]

        if handler not in lvnf.image.handlers:
            raise KeyError("Handler %s not found" % handler)

        self.__handler = handler

    @property
    def lvnf(self):
        return self.__lvnf

    @lvnf.setter
    def lvnf(self, value):
        self.__lvnf = UUID(str(value))

    def to_dict(self):
        """Return a JSON-serializable representation of this object."""

        out = super().to_dict()

        out['lvnf'] = self.lvnf
        out['handler'] = self.handler
        out['retcode'] = self.retcode
        out['samples'] = self.samples

        return out

    def run_once(self):
        """Send out handler requests."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        lvnfs = RUNTIME.tenants[self.tenant_id].lvnfs

        if self.lvnf not in lvnfs:
            self.log.error("LVNF %s not found.", self.lvnf)
            self.unload()
            return

        lvnf = lvnfs[self.lvnf]

        if not lvnf.cpp.connection:
            self.log.info("CPP %s not connected", lvnf.cpp.addr)
            self.unload()
            return

        handler_req = {'module_id': self.module_id,
                       'lvnf_id': self.lvnf,
                       'tenant_id': self.tenant_id,
                       'handler': lvnf.image.handlers[self.handler]}

        lvnf.cpp.connection.send_message(PT_LVNF_GET_REQUEST, handler_req)

    def handle_response(self, response):
        """Handle an incoming LVNF_GET_RESPONSE message.
        Args:
            response, a LVNF_GET_RESPONSE message
        Returns:
            None
        """

        tenant_id = UUID(response['tenant_id'])
        lvnf_id = UUID(response['lvnf_id'])

        tenant = RUNTIME.tenants[tenant_id]

        if lvnf_id not in tenant.lvnfs:
            return

        # update this object
        if response['retcode'] != 200:
            error = "%s (%s)" % (response['retcode'], response['samples'])
            self.log.error("Error accessing %s: %s", self.handler, error)
            return

        self.retcode = response['retcode']
        self.samples = response['samples']

        # call callback
        self.handle_callback(self)


class LVNFGetWorker(ModuleLVNFPWorker):
    """ Counter worker. """

    pass


def lvnf_get(**kwargs):
    """Create a new module."""

    return RUNTIME.components[LVNFGetWorker.__module__].add_module(**kwargs)


def bound_lvnf_get(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    kwargs['lvnf'] = self.lvnf
    return lvnf_get(**kwargs)

setattr(LVNF, LVNFGet.MODULE_NAME, bound_lvnf_get)


def launch():
    """ Initialize the module. """

    return LVNFGetWorker(LVNFGet, PT_LVNF_GET_RESPONSE)
