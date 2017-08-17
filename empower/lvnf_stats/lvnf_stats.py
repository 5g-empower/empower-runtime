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

"""LVNF stats gathering module."""

from uuid import UUID

from empower.core.lvnf import LVNF
from empower.core.module import Module
from empower.lvnf_stats import PT_LVNF_STATS_RESPONSE
from empower.lvnf_stats import PT_LVNF_STATS_REQUEST
from empower.lvnfp.lvnfpserver import ModuleLVNFPWorker

from empower.main import RUNTIME


class LVNFStats(Module):
    """LVNFStats object."""

    MODULE_NAME = "lvnf_stats"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvnf']

    # parameters
    _lvnf = None

    # data structure
    stats = {}

    @property
    def lvnf(self):
        """Return lvnf."""

        return self._lvnf

    @lvnf.setter
    def lvnf(self, value):
        """Set lvnf."""

        self._lvnf = UUID(value)

    def __eq__(self, other):

        return super().__eq__(other) and self.lvnf == other.lvnf

    def to_dict(self):
        """Return a JSON-serializable representation of this object."""

        out = super().to_dict()

        out['lvnf'] = self.lvnf
        out['stats'] = self.stats

        return out

    def run_once(self):
        """Send out stats requests."""

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

        stats = {'module_id': self.module_id,
                 'lvnf_id': self.lvnf,
                 'tenant_id': self.tenant_id}

        lvnf.cpp.connection.send_message(PT_LVNF_STATS_REQUEST, stats)

    def handle_response(self, response):
        """Handle an incoming STATS_RESPONSE message.
        Args:
            response, a STATS_RESPONSE message
        Returns:
            None
        """

        tenant_id = UUID(response['tenant_id'])
        lvnf_id = UUID(response['lvnf_id'])

        tenant = RUNTIME.tenants[tenant_id]

        if lvnf_id not in tenant.lvnfs:
            return

        # update cache
        lvnf = RUNTIME.tenants[tenant_id].lvnfs[lvnf_id]
        lvnf.stats = response['stats']

        # update this object
        self.stats = response['stats']

        # call callback
        self.handle_callback(self)


class LVNFStatsWorker(ModuleLVNFPWorker):
    """ Counter worker. """

    pass


def lvnf_stats(**kwargs):
    """Create a new module."""

    return RUNTIME.components[LVNFStatsWorker.__module__].add_module(**kwargs)


def bound_lvnf_stats(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    kwargs['lvnf'] = self.lvnf
    return lvnf_stats(**kwargs)

setattr(LVNF, LVNFStats.MODULE_NAME, bound_lvnf_stats)


def launch():
    """ Initialize the module. """

    return LVNFStatsWorker(LVNFStats, PT_LVNF_STATS_RESPONSE)
