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
from empower.vbsp import PRT_VBSP_REGISTER
from empower.vbsp.vbspserver import ModuleVBSPEventWorker

from empower.main import RUNTIME


class VBSUp(ModuleTrigger):
    """VBSUp worker."""

    MODULE_NAME = "vbsup"

    def run_once(self):
        """This will be executed only once after initialization."""

        for vbs in RUNTIME.tenants[self.tenant_id].vbses.values():

            if not vbs.connection:
                continue

            vbs.connection.send_register_message_to_self()

    def handle_response(self, vbs):
        """ Handle a REGISTER message.

        Args:
            vbs, a VBS object

        Returns:
            None
        """

        vbses = RUNTIME.tenants[self.tenant_id].vbses

        if vbs.addr not in vbses:
            return

        self.handle_callback(vbs)


class VBSUpWorker(ModuleVBSPEventWorker):
    """ Counter worker. """

    pass


def vbsup(**kwargs):
    """Create a new module."""

    return RUNTIME.components[VBSUpWorker.__module__].add_module(**kwargs)


def app_vbsup(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return vbsup(**kwargs)


setattr(EmpowerApp, VBSUp.MODULE_NAME, app_vbsup)


def launch():
    """Initialize the module."""

    return VBSUpWorker(VBSUp, PRT_VBSP_REGISTER)
