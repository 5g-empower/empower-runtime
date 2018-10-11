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

import tornado.ioloop
import empower.logger

from empower.core.resourcepool import ResourcePool
from empower.core.cellpool import CellPool
from empower.lvapp.lvappserver import LVAPPServer
from empower.lvapp import PT_LVAP_JOIN

from empower.main import RUNTIME

DEFAULT_PERIOD = 5000


class EmpowerApp:
    """EmpowerApp base app class."""

    def __init__(self, tenant_id, **kwargs):

        self.__tenant_id = tenant_id
        self.__every = DEFAULT_PERIOD
        self.log = empower.logger.get_logger()
        self.worker = None

        for param in kwargs:
            setattr(self, param, kwargs[param])

        # uncommen the following lines after updating the event handling
        #self._register_lvapp_event(PT_LVAP_JOIN, self.lvap_join)

    @classmethod
    def _register_lvapp_event(cls, message, handler):
        server = RUNTIME.components[LVAPPServer.__module__]
        server.register_message(message, None, handler)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = {}

        output['name'] = self.__module__
        output['every'] = self.every
        output['tenant_id'] = self.tenant_id

        return output

    def ue_leave(self, ue):
        """Called when a UE leaves a tenant."""

        pass

    def ue_join(self, ue):
        """Called when a UE joins a tenant."""

        pass

    def lvnf_leave(self, lvap):
        """Called when an LVNF leaves a tenant."""

        pass

    def lvnf_join(self, lvap):
        """Called when an LVNF joins a tenant."""

        pass

    def lvap_leave(self, lvap):
        """Called when an LVAP leavess a tenant."""

        pass

    def lvap_join(self, lvap):
        """Called when an LVAP joins a tenant."""

        pass

    def lvap_handover(self, lvap, source_blocks):
        """Called when an LVAP completes a handover."""

        pass

    def vbs_down(self, vbs):
        """Called when a VBS disconnects to the controller."""

        pass

    def vbs_up(self, vbs):
        """Called when a VBS connects from the controller."""

        pass

    def cpp_down(self, cpp):
        """Called when a CPP disconnects to the controller."""

        pass

    def cpp_up(self, cpp):
        """Called when a CPP connects from the controller."""

        pass

    def wtp_down(self, wtp):
        """Called when a WTP disconnects to the controller."""

        pass

    def wtp_up(self, wtp):
        """Called when a WTP connects from the controller."""

        pass

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

        self.worker = \
            tornado.ioloop.PeriodicCallback(self.loop, self.every)
        self.worker.start()

    def stop(self):
        """Stop control loop."""

        self.worker.stop()

    def loop(self):
        """Control loop."""

        pass

    def vbses(self):
        """Return VBSPs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        return RUNTIME.tenants[self.tenant_id].vbses.values()

    def vbs(self, addr):
        """Return a particular VBSP in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if addr not in RUNTIME.tenants[self.tenant_id].vbses:
            return None

        return RUNTIME.tenants[self.tenant_id].vbses[addr]

    def lvaps(self, block=None):
        """Return LVAPs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        lvaps = RUNTIME.tenants[self.tenant_id].lvaps.values()

        if not block:
            return lvaps

        return [x for x in lvaps if x.blocks[0] == block]

    def lvap(self, addr):
        """Return a particular LVAP in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if addr not in RUNTIME.tenants[self.tenant_id].lvaps:
            return None

        return RUNTIME.tenants[self.tenant_id].lvaps[addr]

    def ues(self, vbs=None):
        """Return UEs in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        ues = RUNTIME.tenants[self.tenant_id].ues.values()

        if not vbs:
            return ues

        return [x for x in ues if x.vbs == vbs]

    def ue(self, ue_id):
        """Return a particular UE in this tenant."""

        if self.tenant_id not in RUNTIME.tenants:
            return None

        if ue_id not in RUNTIME.tenants[self.tenant_id].ues:
            return None

        return RUNTIME.tenants[self.tenant_id].ues[ue_id]

    def cells(self):
        """Return all available cells in this tenant."""

        # Initialize the Resource Pool
        pool = CellPool()

        # Update the pool with all the available Cells
        for vbs in self.vbses():
            for cell in vbs.cells.values():
                pool.append(cell)

        return pool

    def blocks(self):
        """Return all ResourseBlocks in this Tenant."""

        # Initialize the Resource Pool
        pool = ResourcePool()

        # Update the pool with all the available ResourseBlocks
        for wtp in self.wtps():
            for block in wtp.supports:
                pool.append(block)

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
