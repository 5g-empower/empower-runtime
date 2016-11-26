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
from empower.vbsp.vbspserver import ModuleVBSPEventWorker
from empower.vbsp import PRT_UE_JOIN

from empower.main import RUNTIME


class UEJoin(ModuleTrigger):
    """UEJoin."""

    MODULE_NAME = "uejoin"

    def handle_response(self, ue):
        """ Handle an UE_JOIN message.
        Args:
            ue, an UE object
        Returns:
            None
        """

        ues = RUNTIME.tenants[self.tenant_id].ues

        if ue.addr not in ues:
            return

        self.handle_callback(ue)


class UEJoinWorker(ModuleVBSPEventWorker):
    """UEJoin."""

    pass


def uejoin(**kwargs):
    """Create a new module."""

    return RUNTIME.components[UEJoinWorker.__module__].add_module(**kwargs)


def app_uejoin(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return uejoin(**kwargs)


setattr(EmpowerApp, UEJoin.MODULE_NAME, app_uejoin)


def launch():
    """Initialize the module."""

    return UEJoinWorker(UEJoin, PRT_UE_JOIN)
