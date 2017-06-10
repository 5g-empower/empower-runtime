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

"""EmPOWER base app class."""

import uuid
import tornado.ioloop
import empower.logger

from empower.core.resourcepool import ResourcePool
from empower.core.lvnf import LVNF

from empower.main import RUNTIME

DEFAULT_PERIOD = 5000


class EmpowerApp(object):
    """EmpowerApp base app class."""

    def __init__(self, tenant_id, **kwargs):

        self.__tenant_id = tenant_id
        self.__every = DEFAULT_PERIOD
        self.app_name = self.__module__.split(".")[-1]
        self.params = []
        self.log = empower.logger.get_logger()
        self.worker = None

        for param in kwargs:
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

        self.log.info("Setting control loop interval to %ums", int(value))
        self.__every = int(value)

    def start(self):
        """Start control loop."""

        self.worker = tornado.ioloop.PeriodicCallback(self.loop, self.every)
        self.worker.start()

    def stop(self):
        """Stop control loop."""

        self.worker.stop()

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        params = {}

        params['app_name'] = self.app_name
        params['tenant_id'] = self.tenant_id
        params['ui_url'] = "/apps/tenants/%s/%s/" % \
            (self.tenant_id, self.app_name)
        params['params'] = self.params

        for param in self.params:
            params[param] = getattr(self, param)

        return params

    def loop(self):
        """Control loop."""

        pass

    def vbsps(self):
        """Return VBSPs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        return RUNTIME.tenants[self.tenant_id].vbsps.values()

    def vbsp(self, addr):
        """Return a particular VBSP in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if addr not in RUNTIME.tenants[self.tenant_id].vbsps:
            return None

        return RUNTIME.tenants[self.tenant_id].vbsps[addr]

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

    def blocks(self, lvap=None, limit=None):
        """Return all blocks in this Tenant."""

        # Initialize the Resource Pool
        pool = ResourcePool()

        # Update the Resource Pool with all
        # the available Resourse Blocks
        for wtp in self.wtps():
            for block in wtp.supports:
                pool.add(block)

        return pool

    def wtps(self):
        """Return WTPs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        return RUNTIME.tenants[self.tenant_id].wtps.values()

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

    def spawn_lvnf(self, image, cpp, lvnf_id=None):
        """Spawn a new LVNF on the specified CPP."""

        if not lvnf_id:
            lvnf_id = uuid.uuid4()
        else:
            lvnf_id = uuid.UUID(lvnf_id)

        lvnf = LVNF(lvnf_id=lvnf_id,
                    tenant_id=self.tenant_id,
                    image=image,
                    cpp=cpp)

        lvnf.start()

    def delete_lvnf(self, lvnf_id):
        """Remove LVNF."""

        tenant = RUNTIME.tenants[self.tenant_id]
        lvnf = tenant.lvnfs[lvnf_id]

        lvnf.stop()
