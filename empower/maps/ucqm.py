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

"""User channel quality map module."""

from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.app import EmpowerApp
from empower.maps.maps import POLLER_RESPONSE
from empower.maps.maps import Maps

from empower.main import RUNTIME

PT_POLLER_REQUEST = 0x25
PT_POLLER_RESPONSE = 0x26


class UCQM(Maps):
    """User Channel Quality Maps."""

    MODULE_NAME = "ucqm"
    PT_REQUEST = PT_POLLER_REQUEST


class UCQMWorker(ModuleLVAPPWorker):
    """User channel quality map worker."""

    pass


def ucqm(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[UCQMWorker.__module__]
    return worker.add_module(**kwargs)


def bound_ucqm(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return ucqm(**kwargs)

setattr(EmpowerApp, UCQM.MODULE_NAME, bound_ucqm)


def launch():
    """ Initialize the module. """

    return UCQMWorker(UCQM, PT_POLLER_RESPONSE, POLLER_RESPONSE)
