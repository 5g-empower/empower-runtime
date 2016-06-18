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
from empower.core.module import Module
from empower.vbspp import PRT_VBSP_REGISTER
from empower.vbspp.vbspserver import ModuleVBSPPEventWorker

from empower.main import RUNTIME


class VBSPUp(Module):
    """VBSPUp worker."""

    MODULE_NAME = "vbspup"

    def handle_response(self, vbsp):
        """ Handle a REGISTER message.

        Args:
            vbsp, a VBSP object

        Returns:
            None
        """

        vbsps = RUNTIME.tenants[self.tenant_id].vbsps

        if vbsp.addr not in vbsps:
            return

        vbsp = vbsps[vbsp.addr]

        self.handle_callback(vbsp)


class VBSPUpWorker(ModuleVBSPPEventWorker):
    """ Counter worker. """

    pass


def vbspup(**kwargs):
    """Create a new module."""

    return RUNTIME.components[VBSPUpWorker.__module__].add_module(**kwargs)


def app_vbspup(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return vbspup(**kwargs)


setattr(EmpowerApp, VBSPUp.MODULE_NAME, app_vbspup)


def launch():
    """Initialize the module."""

    return VBSPUpWorker(VBSPUp, PRT_VBSP_REGISTER)
