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
from empower.lvnfp import PT_LVNF_LEAVE

from empower.main import RUNTIME


class LVNFLeave(ModuleTrigger):
    """LVNFLeave worker."""

    MODULE_NAME = "lvnfleave"

    def handle_response(self, lvnf):
        """ Handle an LEAVE message.

        Args:
            lvnf, a LVNF object

        Returns:
            None
        """

        lvnfs = RUNTIME.tenants[self.tenant_id].lvnfs

        if lvnf.lvnf_id not in lvnfs:
            return

        self.handle_callback(lvnf)


class LVNFLeaveWorker(ModuleLVNFPEventWorker):
    """ Counter worker. """

    pass


def lvnfleave(**kwargs):
    """Create a new module."""

    return RUNTIME.components[LVNFLeaveWorker.__module__].add_module(**kwargs)


def app_lvnfleave(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return lvnfleave(**kwargs)


setattr(EmpowerApp, LVNFLeave.MODULE_NAME, app_lvnfleave)


def launch():
    """Initialize the module."""

    return LVNFLeaveWorker(LVNFLeave, PT_LVNF_LEAVE)
