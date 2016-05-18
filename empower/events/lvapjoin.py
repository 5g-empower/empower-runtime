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

"""LVAP join event module."""

from empower.core.module import ModuleLVAPPEventWorker
from empower.core.module import Module
from empower.lvapp import PT_LVAP_JOIN

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class LVAPJoin(Module):
    """LVAPJoin."""

    MODULE_NAME = "lvapjoin"

    def handle_response(self, lvap):
        """ Handle an LVAL_JOIN message.
        Args:
            lvap, an LVAP object
        Returns:
            None
        """

        lvaps = RUNTIME.tenants[self.tenant_id].lvaps

        if lvap.addr not in lvaps:
            return

        self.handle_callback(lvap)


class LVAPJoinWorker(ModuleLVAPPEventWorker):
    """LVAPJoin."""

    pass


def lvapjoin(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[LVAPJoinWorker.__module__]
    return worker.add_module(**kwargs)


def remove_lvapjoin(**kwargs):
    """Remove module."""

    worker = RUNTIME.components[LVAPJoinWorker.__module__]
    worker.remove_module(kwargs['module_id'])


def launch():
    """Initialize the module."""

    return LVAPJoinWorker(LVAPJoin, PT_LVAP_JOIN)
