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
from empower.lvnfp import PT_BYE

from empower.main import RUNTIME


class CPPDown(ModuleTrigger):
    """CPPDown worker."""

    MODULE_NAME = "cppdown"

    def handle_response(self, register):
        """ Handle an REGISTER message.

        Args:
            cpp, a CPP object

        Returns:
            None
        """

        cpps = RUNTIME.tenants[self.tenant_id].cpps

        if register['addr'] not in cpps:
            return

        cpp = cpps[register['addr']]

        self.handle_callback(cpp)


class CPPDownWorker(ModuleLVNFPEventWorker):
    """ Counter worker. """

    pass


def cppdown(**kwargs):
    """Create a new module."""

    return RUNTIME.components[CPPDownWorker.__module__].add_module(**kwargs)


def app_cppdown(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return cppdown(**kwargs)


setattr(EmpowerApp, CPPDown.MODULE_NAME, app_cppdown)


def launch():
    """Initialize the module."""

    return CPPDownWorker(CPPDown, PT_BYE)
