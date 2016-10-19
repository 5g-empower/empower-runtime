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
from empower.lvapp.lvappserver import ModuleLVAPPEventWorker
from empower.lvapp import PT_LVAP_JOIN

from empower.main import RUNTIME


class LVAPJoin(ModuleTrigger):
    """LVAPJoin."""

    MODULE_NAME = "lvapjoin"

    def handle_response(self, lvap):
        """ Handle an LVAL_JOIN message.
        Args:
            lvap, an LVAP object
        Returns:
            None
        """

        lvaps = RUNTIME.tenants[self.tenant_id].lvaps

        if lvap.addr not in lvaps:
            return

        self.handle_callback(lvap)


class LVAPJoinWorker(ModuleLVAPPEventWorker):
    """LVAPJoin."""

    pass


def lvapjoin(**kwargs):
    """Create a new module."""

    return RUNTIME.components[LVAPJoinWorker.__module__].add_module(**kwargs)


def app_lvapjoin(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return lvapjoin(**kwargs)


setattr(EmpowerApp, LVAPJoin.MODULE_NAME, app_lvapjoin)


def launch():
    """Initialize the module."""

    return LVAPJoinWorker(LVAPJoin, PT_LVAP_JOIN)
