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

"""WTP up event module."""

from empower.core.module import ModuleEventWorker
from empower.core.module import Module
from empower.core.module import handle_callback
from empower.lvapp.lvappserver import LVAPPServer
from empower.lvapp import PT_CAPS_RESPONSE
from empower.datatypes.etheraddress import EtherAddress

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class WTPUp(Module):
    """WTPUp worker."""

    def handle_response(self, caps_response):
        """ Handle an CAPS_RESPONSE message.

        Args:
            caps_response, a CAPS_RESPONSE message

        Returns:
            None
        """

        addr = EtherAddress(caps_response.wtp)
        wtps = RUNTIME.tenants[self.tenant_id].wtps

        if addr not in wtps:
            return

        wtp = wtps[addr]

        handle_callback(wtp, self)


class WTPUpWorker(ModuleEventWorker):
    """ Counter worker. """

    MODULE_NAME = "wtpup"
    MODULE_TYPE = WTPUp
    PT_TYPE = PT_CAPS_RESPONSE
    PT_PACKET = None


def wtpup(*args, **kwargs):
    """Create a new module.

    Args:
        kwargs: keyword arguments for the module.

    Returns:
        None
    """

    worker = RUNTIME.components[WTPUpWorker.__module__]
    kwargs['worker'] = worker
    kwargs['module_type'] = worker.MODULE_NAME
    new_module = worker.add_module(**kwargs)

    return new_module


def remove_wtpup(*args, **kwargs):
    """Remove module."""

    worker = RUNTIME.components[WTPUpWorker.__module__]
    worker.remove_module(kwargs['module_id'])


def launch():
    """ Initialize the module. """

    worker = WTPUpWorker(LVAPPServer.__module__)
    return worker
