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

"""User channel quality map module."""

from empower.core.module import ModuleLVAPPWorker
from empower.core.app import EmpowerApp
from empower.maps.maps import POLLER_RESPONSE
from empower.maps.maps import Maps

from empower.main import RUNTIME

PT_POLLER_REQUEST = 0x25
PT_POLLER_RESPONSE = 0x26


class UCQM(Maps):
    """User Channel Quality Maps."""

    MODULE_NAME = "ucqm"
    PT_REQUEST = PT_POLLER_REQUEST


class UCQMWorker(ModuleLVAPPWorker):
    """User channel quality map worker."""

    pass


def ucqm(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[UCQMWorker.__module__]
    return worker.add_module(**kwargs)


def bound_ucqm(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return ucqm(**kwargs)

setattr(EmpowerApp, UCQM.MODULE_NAME, bound_ucqm)


def launch():
    """ Initialize the module. """

    return UCQMWorker(UCQM, PT_POLLER_RESPONSE, POLLER_RESPONSE)
