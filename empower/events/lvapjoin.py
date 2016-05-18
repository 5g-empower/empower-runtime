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
from empower.core.module import handle_callback
from empower.lvapp.lvappserver import LVAPPServer
from empower.lvapp import PT_LVAP_JOIN

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class LVAPJoin(Module):
    """ LvapUp worker. """

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

        handle_callback(lvap, self)


class LVAPJoinWorker(ModuleLVAPPEventWorker):
    """ Counter worker. """

    MODULE_NAME = "lvapjoin"
    MODULE_TYPE = LVAPJoin


def lvapjoin(*args, **kwargs):
    """Create a new module.

    Args:
        kwargs: keyword arguments for the module.

    Returns:
        None
    """

    worker = RUNTIME.components[LVAPJoinWorker.__module__]
    kwargs['worker'] = worker
    kwargs['module_type'] = worker.MODULE_NAME
    new_module = worker.add_module(**kwargs)

    return new_module


def remove_lvapjoin(*args, **kwargs):
    """Remove module."""

    worker = RUNTIME.components[LVAPJoinWorker.__module__]
    worker.remove_module(kwargs['module_id'])


def launch():
    """ Initialize the module. """

    worker = LVAPJoinWorker(PT_LVAP_JOIN)
    return worker
