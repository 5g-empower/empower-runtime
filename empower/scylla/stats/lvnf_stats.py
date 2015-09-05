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

from empower.core.module import ModuleWorker
from empower.core.module import ModuleHandler
from empower.core.module import Module
from empower.core.module import bind_module
from empower.core.module import handle_callback
from empower.scylla.stats import PT_LVNF_STATS_REQUEST
from empower.scylla.stats import PT_LVNF_STATS_RESPONSE
from empower.scylla.lvnfp.lvnfpserver import LVNFPServer
from empower.core.restserver import RESTServer

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class LVNFStats(Module):
    """LVNFStats object."""

    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvnf_id']

    def __init__(self):

        super().__init__()

        self.__lvnf_id = None
        self.stats = None

    def __eq__(self, other):

        return super().__eq__(other) and \
               self.lvnf_id == other.lvnf_id

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
        out['stats'] = self.stats

        return out

    def run_once(self):
        """Send out stats requests."""

        worker = RUNTIME.components[self.worker.__module__]
        worker.send_lvnf_stats_request(self)


class LVNFStatsHandler(ModuleHandler):
    pass


class LVNFStatsWorker(ModuleWorker):
    """LVNFStats worker."""

    MODULE_NAME = "lvnf_stats"
    MODULE_HANDLER = LVNFStatsHandler
    MODULE_TYPE = LVNFStats

    def send_lvnf_stats_request(self, stats):
        """Send a lvnf stats request message."""

        # start profiling
        stats.tic()

        if stats.tenant_id not in RUNTIME.tenants:
            self.remove_module(stats.tenant_id, stats.module_id)
            return

        tenant = RUNTIME.tenants[stats.tenant_id]

        if stats.lvnf_id not in tenant.lvnfs:
            LOG.error("LVNF %s not found." % stats.lvnf_id)
            self.remove_module(stats.tenant_id, stats.module_id)
            return

        lvnf = tenant.lvnfs[stats.lvnf_id]

        if not lvnf.cpp.connection:
            return

        stats_req = {'lvnf_stats_id': stats.module_id,
                     'lvnf_id': stats.lvnf_id,
                     'tenant_id': stats.tenant_id}

        lvnf.cpp.connection.send_message(PT_LVNF_STATS_REQUEST, stats_req)

    def handle_lvnf_stats_response(self, stats_response):
        """Handle an incoming stats response message.
        Args:
            stats_response, a stats response message
        Returns:
            None
        """

        if stats_response['lvnf_stats_id'] not in self.modules:
            return

        stats = self.modules[stats_response['lvnf_stats_id']]

        # stop profiling
        stats.toc()

        tenant_id = UUID(stats_response['tenant_id'])
        lvnf_id = UUID(stats_response['lvnf_id'])

        tenant = RUNTIME.tenants[tenant_id]

        if lvnf_id not in tenant.lvnfs:
            return

        stats.stats = stats_response['stats']

        # handle callback
        if stats.callback:
            handle_callback(stats, stats)


bind_module(LVNFStatsWorker)


def launch():
    """Initialize the module."""

    lvnf_server = RUNTIME.components[LVNFPServer.__module__]
    rest_server = RUNTIME.components[RESTServer.__module__]

    worker = LVNFStatsWorker(rest_server)
    lvnf_server.register_message(PT_LVNF_STATS_RESPONSE,
                                 None,
                                 worker.handle_lvnf_stats_response)

    return worker
