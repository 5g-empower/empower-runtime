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

"""CPP up event module."""

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import ModuleHandler
from empower.core.module import ModuleWorker
from empower.core.module import Module
from empower.restserver.restserver import RESTServer
from empower.lvnfp.lvnfpserver import LVNFPServer
from empower.core.module import ModuleLVAPPEventWorker
from empower.lvnfp import PT_REGISTER

from empower.main import RUNTIME


class CPPUp(Module):
    """CPPUp worker."""

    MODULE_NAME = "cppup"

    def on_cpp_up(self, register):
        """ Handle an REGISTER message.

        Args:
            register, a REGISTER message

        Returns:
            None
        """

        print(register)

        return

        for event in list(self.modules.values()):

            if event.tenant_id not in RUNTIME.tenants:
                return

            addr = EtherAddress(register['addr'])
            cpps = RUNTIME.tenants[event.tenant_id].cpps

            if addr not in cpps:
                return

            LOG.info("Event: CPP Up %s", addr)

            handle_callback(cpps[addr], event)


class CPPUpWorker(ModuleLVAPPEventWorker):
    """ Counter worker. """

    pass


def cppup(**kwargs):
    """Create a new module."""

    return RUNTIME.components[CPPUpWorker.__module__].add_module(**kwargs)


def app_cppup(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return cppup(**kwargs)


setattr(EmpowerApp, CPPUp.MODULE_NAME, app_cppup)


def launch():
    """Initialize the module."""

    return CPPUpWorker(CPPUp, PT_REGISTER)
