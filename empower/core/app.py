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

import empower.logger

from empower.restserver.restserver import RESTServer
from empower.restserver.restserver import BaseHandler

from empower.main import RUNTIME

DEFAULT_PERIOD = 5000


class EmpowerAppHomeHandler(BaseHandler):
    """Web UI Handler.

    Base Web UI handler, sub-class to implement app-specific web UI handlers.
    Templates must be put in the /templates/<app name>/ sub-directory. Static
    files must be put in the /static/<app name>/.
    """

    def get(self):

        page = "apps/%s/index.html" % self.server.__module__
        self.render(page, tenant_id=self.server.tenant_id)


class EmpowerApp(object):
    """EmpowerApp base app class."""

    def __init__(self, tenant_id, **kwargs):

        self.__tenant_id = tenant_id
        self.__every = DEFAULT_PERIOD
        self.ui_url = None
        self.params = []
        self.log = empower.logger.get_logger()
        self.worker = tornado.ioloop.PeriodicCallback(self.loop, self.every)

        self.ui_url = r"/apps/%s/?" % self.__module__
        handler = (self.ui_url, EmpowerAppHomeHandler, dict(server=self))
        rest_server = RUNTIME.components[RESTServer.__module__]
        rest_server.add_handler(handler)

        for param in kwargs:
            if hasattr(self, param):
                setattr(self, param, kwargs[param])
                self.params.append(param)

    @property
    def tenant_id(self):
        """Return tenant_id."""

        return self.__tenant_id

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

        self.log.info("Setting control loop interval to %u", value)
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

        params['tenant_id'] = self.tenant_id
        params['ui_url'] = self.ui_url
        params['params'] = self.params

        for param in self.params:
            params[param] = getattr(self, param)

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
