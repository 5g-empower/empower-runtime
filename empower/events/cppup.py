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

from empower.core.app import EmpowerApp
from empower.core.module import ModuleTrigger
from empower.lvnfp.lvnfpserver import ModuleLVNFPEventWorker
from empower.lvnfp import PT_REGISTER

from empower.main import RUNTIME


class CPPUp(ModuleTrigger):
    """CPPUp worker."""

    MODULE_NAME = "cppup"

    def run_once(self):
        """This will be executed only once after initialization."""

        for cpp in RUNTIME.tenants[self.tenant_id].cpps.values():

            if not cpp.connection:
                continue

            cpp.connection.send_register_message_to_self()

    def handle_response(self, register):
        """ Handle an REGISTER message.

        Args:
            register, a register message

        Returns:
            None
        """

        cpps = RUNTIME.tenants[self.tenant_id].cpps

        if register['addr'] not in cpps:
            return

        cpp = cpps[register['addr']]

        self.handle_callback(cpp)


class CPPUpWorker(ModuleLVNFPEventWorker):
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
