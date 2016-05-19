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

from empower.core.app import EmpowerApp
from empower.core.module import Module
from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import ModuleLVAPPEventWorker
from empower.lvapp import PT_CAPS_RESPONSE

from empower.main import RUNTIME


class WTPUp(Module):
    """WTPUp worker."""

    MODULE_NAME = "wtpup"

    def handle_response(self, caps_response):
        """ Handle an CAPS_RESPONSE message.

        Args:
            caps_response, a CAPS_RESPONSE message

        Returns:
            None
        """

        addr = EtherAddress(caps_response.wtp)

        if addr not in RUNTIME.tenants[self.tenant_id].wtps:
            return

        wtp = RUNTIME.tenants[self.tenant_id].wtps[addr]

        self.handle_callback(wtp)


class WTPUpWorker(ModuleLVAPPEventWorker):
    """ Counter worker. """

    pass


def wtpup(**kwargs):
    """Create a new module."""

    return RUNTIME.components[WTPUpWorker.__module__].add_module(**kwargs)


def app_wtpup(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return wtpup(**kwargs)


setattr(EmpowerApp, WTPUp.MODULE_NAME, app_wtpup)


def launch():
    """Initialize the module."""

    return WTPUpWorker(WTPUp, PT_CAPS_RESPONSE)
