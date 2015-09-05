#!/usr/bin/env python3
#
# Copyright (c) 2016, Roberto Riggio
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

"""EmPOWER base app class."""

import tornado.ioloop
import json

from uuid import UUID
from empower.core.jsonserializer import EmpowerEncoder
from empower.core.restserver import EmpowerAPIHandlerUsers
from empower.core.restserver import RESTServer
from empower.core.restserver import BaseHandler

from empower.main import RUNTIME

DEFAULT_PERIOD = 5000


class EmpowerAppHomeHandler(BaseHandler):
    """Web UI Handler.

    Base Web UI handler, sub-class to implement app-specific web UI handlers.
    Templates must be put in the /templates/<app name>/ sub-directory. Static
    files must be put in the /static/<app name>/. Note that <app name> is
    defined by the MODULE_NAME variable in the EmpowerApp instance.
    """

    PAGE = None
    HANDLERS = []

    def get(self):
        self.render(self.PAGE, tenant_id=self.server.tenant_id)


class EmpowerAppHandler(EmpowerAPIHandlerUsers):
    """REST Handler.

    Base REST handler, sub-class to implement app-specific REST handlers.
    The REST interface is available at /apps/tenants/<tenant id>/<app name>/.
    """

    HANDLERS = []

    def get(self, *args, **kwargs):
        """Get method handler.

        This method is used by apps in order to export their data structures.
        By default this REST method calls the to_dict() method of the web app
        object and returns its JSON serialization.

        Args:
            None

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/conflicts
        """

        try:
            self.write(json.dumps(self.server.to_dict(), cls=EmpowerEncoder))
        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(200, None)


class EmpowerApp(object):
    """EmpowerApp base app class.

    Applications must sub class EmpowerApp and must override MODULE_NAME with
    a unique name for the application. Applications can also override
    MODULE_HANDLER and MODULE_HOME_HANDLER in order to enable the rest
    interface and the web ui respectivelly.
    """

    MODULE_NAME = None
    MODULE_HANDLER = None
    MODULE_HOME_HANDLER = None

    def __init__(self, tenant_id, every, **kwargs):

        self.tenant_id = tenant_id
        self.every = every
        self.ui = None
        self.rest = None

        self.worker = tornado.ioloop.PeriodicCallback(self.loop, self.every)

        if self.MODULE_NAME and self.MODULE_HANDLER:

            module = (self.tenant_id, self.MODULE_NAME)

            self.MODULE_HANDLER.HANDLERS.\
                append(r"/api/v1/tenants/%s/%s/?" % module)

            self.rest = "/api/v1/tenants/%s/%s/?" % module

            rest_server = RUNTIME.components[RESTServer.__module__]

            rest_server.add_handler_class(self.MODULE_HANDLER, self)

        if self.MODULE_NAME and self.MODULE_HOME_HANDLER:

            module = (self.tenant_id, self.MODULE_NAME)

            self.MODULE_HOME_HANDLER.PAGE = \
                "apps/%s/index.html" % self.MODULE_NAME

            self.MODULE_HOME_HANDLER.HANDLERS.\
                append(r"/apps/tenants/%s/%s/?" % module)

            self.ui = "/apps/tenants/%s/%s/?" % module

            rest_server = RUNTIME.components[RESTServer.__module__]

            rest_server.add_handler_class(self.MODULE_HOME_HANDLER, self)

        for param in kwargs:
            if hasattr(self, param):
                setattr(self, param, kwargs[param])

    @property
    def tenant_id(self):
        """Return tenant_id."""

        return self.__tenant_id

    @tenant_id.setter
    def tenant_id(self, tenant_id):
        """Set tenant_id."""

        self.__tenant_id = UUID(str(tenant_id))

    @property
    def tenant(self):
        """Return tenant instance."""

        return RUNTIME.tenants[self.tenant_id]

    @property
    def every(self):
        """Return loop period."""

        return self.__every

    @every.setter
    def every(self, value):
        """Set loop period."""

        self.__every = int(value)

    def start(self):
        """Start control loop."""

        self.worker.start()

    def stop(self):
        """Stop control loop."""

        self.worker.stop()

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        params = {}
        params['every'] = self.every
        params['tenant_id'] = self.tenant_id
        params['ui'] = self.ui
        params['rest'] = self.rest

        return params

    def loop(self):
        """Control loop."""

        pass

    def wtps(self):
        """Return WTPs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        return RUNTIME.tenants[self.tenant_id].wtps.values()

    def lvaps(self):
        """Return LVAPs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        return RUNTIME.tenants[self.tenant_id].lvaps.values()

    def lvap(self, addr):
        """Return a particular LVAP in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if addr not in RUNTIME.tenants[self.tenant_id].lvaps:
            return None

        return RUNTIME.tenants[self.tenant_id].lvaps[addr]

    def wtp(self, addr):
        """Return a particular WTP in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if addr not in RUNTIME.tenants[self.tenant_id].wtps:
            return None

        return RUNTIME.tenants[self.tenant_id].wtps[addr]

    def cpps(self):
        """Return CPPs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        return RUNTIME.tenants[self.tenant_id].cpps.values()

    def cpp(self, addr):
        """Return a particular CPP in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if addr not in RUNTIME.tenants[self.tenant_id].cpps:
            return None

        return RUNTIME.tenants[self.tenant_id].cpps[addr]

    def lvnfs(self):
        """Return LVNFs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        return RUNTIME.tenants[self.tenant_id].lvnfs.values()

    def lvnf(self, addr):
        """Return a particular LVNF in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if addr not in RUNTIME.tenants[self.tenant_id].lvnfs:
            return None

        return RUNTIME.tenants[self.tenant_id].lvnfs[addr]
