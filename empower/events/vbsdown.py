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
from empower.vbsp import PRT_VBSP_BYE
from empower.vbsp.vbspserver import ModuleVBSPEventWorker

from empower.main import RUNTIME


class VBSDown(ModuleTrigger):
    """VBSDown worker."""

    MODULE_NAME = "vbsdown"

    def handle_response(self, vbs):
        """ Handle an BYE message.

        Args:
            vbs, a VBS object

        Returns:
            None
        """

        vbses = RUNTIME.tenants[self.tenant_id].vbses

        if vbs.addr not in vbses:
            return

        self.handle_callback(vbs)


class VBSDownWorker(ModuleVBSPEventWorker):
    """ Counter worker. """

    pass


def vbsdown(**kwargs):
    """Create a new module."""

    return RUNTIME.components[VBSDownWorker.__module__].add_module(**kwargs)


def app_vbsdown(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return vbsdown(**kwargs)


setattr(EmpowerApp, VBSDown.MODULE_NAME, app_vbsdown)


def launch():
    """Initialize the module."""

    return VBSDownWorker(VBSDown, PRT_VBSP_BYE)
