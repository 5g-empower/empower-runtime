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
from empower.lvnfp import PT_LVNF_JOIN

from empower.main import RUNTIME


class LVNFJoin(ModuleTrigger):
    """LVNFJoin worker."""

    MODULE_NAME = "lvnfjoin"

    def handle_response(self, lvnf):
        """ Handle an JOIN message.

        Args:
            lvnf, a LVNF object

        Returns:
            None
        """

        lvnfs = RUNTIME.tenants[self.tenant_id].lvnfs

        if lvnf.lvnf_id not in lvnfs:
            return

        self.handle_callback(lvnf)


class LVNFJoinWorker(ModuleLVNFPEventWorker):
    """ Counter worker. """

    pass


def lvnfjoin(**kwargs):
    """Create a new module."""

    return RUNTIME.components[LVNFJoinWorker.__module__].add_module(**kwargs)


def app_lvnfjoin(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return lvnfjoin(**kwargs)


setattr(EmpowerApp, LVNFJoin.MODULE_NAME, app_lvnfjoin)


def launch():
    """Initialize the module."""

    return LVNFJoinWorker(LVNFJoin, PT_LVNF_JOIN)
