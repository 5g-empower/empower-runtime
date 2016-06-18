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
            return

        lvnfs = RUNTIME.tenants[self.tenant_id].lvnfs

        if self.lvnf not in lvnfs:
            self.log.error("LVNF %s not found.", self.lvnf)
            return

        lvnf = lvnfs[self.lvnf]

        if not lvnf.cpp.connection:
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
