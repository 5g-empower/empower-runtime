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
from empower.lvapp import PT_BYE

from empower.main import RUNTIME


class WTPDown(ModuleTrigger):
    """WTPDown worker."""

    MODULE_NAME = "wtpdown"

    def handle_response(self, wtp):
        """ Handle an BYE message.

        Args:
            wtp, a wtp object

        Returns:
            None
        """

        wtps = RUNTIME.tenants[self.tenant_id].wtps

        if wtp.addr not in wtps:
            return

        self.handle_callback(wtp)


class WTPDownWorker(ModuleLVAPPEventWorker):
    """ Counter worker. """

    pass


def wtpdown(**kwargs):
    """Create a new module."""

    return RUNTIME.components[WTPDownWorker.__module__].add_module(**kwargs)


def app_wtpdown(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return wtpdown(**kwargs)


setattr(EmpowerApp, WTPDown.MODULE_NAME, app_wtpdown)


def launch():
    """Initialize the module."""

    return WTPDownWorker(WTPDown, PT_BYE)
