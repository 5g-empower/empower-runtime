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
from empower.lvapp.lvappserver import ModuleLVAPPEventWorker
from empower.lvapp import PT_CAPS

from empower.main import RUNTIME


class WTPUp(Module):
    """WTPUp worker."""

    MODULE_NAME = "wtpup"

    def handle_response(self, caps):
        """ Handle an CAPS message.

        Args:
            caps, a CAPS message

        Returns:
            None
        """

        wtps = RUNTIME.tenants[self.tenant_id].wtps

        if caps.wtp not in wtps:
            return

        wtp = wtps[caps.wtp]

        self.handle_callback(wtp)


class WTPUpWorker(ModuleLVAPPEventWorker):
    """ Counter worker. """

    pass


def wtpup(**kwargs):
    """Create a new module."""

    return RUNTIME.components[WTPUpWorker.__module__].add_module(**kwargs)


def app_wtpup(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant_id
    return wtpup(**kwargs)


setattr(EmpowerApp, WTPUp.MODULE_NAME, app_wtpup)


def launch():
    """Initialize the module."""

    return WTPUpWorker(WTPUp, PT_CAPS)
