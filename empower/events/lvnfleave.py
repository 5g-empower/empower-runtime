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

"""LVNF leave event module."""

from empower.core.module import ModuleHandler
from empower.core.module import ModuleWorker
from empower.core.module import Module
from empower.core.module import bind_module
from empower.core.module import handle_callback
from empower.restserver.restserver import RESTServer
from empower.lvnfp.lvnfpserver import LVNFPServer
from empower.lvnfp import PT_LVNF_LEAVE

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class LVNFLeaveHandler(ModuleHandler):
    pass


class LVNFLeave(Module):
    pass


class LVNFLeaveWorker(ModuleWorker):
    """LVNFLeave worker."""

    MODULE_NAME = "lvnfleave"
    MODULE_HANDLER = LVNFLeaveHandler
    MODULE_TYPE = LVNFLeave

    def on_lvnf_leave(self, lvnf):
        """ Handle an kvnf leave event.

        Args:
            lvnf, an LVNF instance

        Returns:
            None
        """

        for event in list(self.modules.values()):

            tenant = RUNTIME.tenants[event.tenant_id]

            if lvnf.lvnf_id not in tenant.lvnfs:
                continue

            LOG.info("Event: LVNF Leave %s", lvnf.lvnf_id)

            handle_callback(lvnf, event)


bind_module(LVNFLeaveWorker)


def launch():
    """ Initialize the module. """

    lvnf_server = RUNTIME.components[LVNFPServer.__module__]
    rest_server = RUNTIME.components[RESTServer.__module__]

    worker = LVNFLeaveWorker(rest_server)
    lvnf_server.register_message(PT_LVNF_LEAVE, None, worker.on_lvnf_leave)

    return worker
