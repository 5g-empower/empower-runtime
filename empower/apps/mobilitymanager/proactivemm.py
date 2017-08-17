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

"""Reactive mobility manager."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class ProactiveMobilityManager(EmpowerApp):
    """Reactive mobility manager.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.mobilitymanager.proactivemm \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26
    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)

        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        # Start polling WTP
        for block in wtp.supports:
            self.ucqm(block=block, every=self.every)

    def loop(self):
        """ Periodic job. """

        for lvap in self.lvaps():
            lvap.blocks = self.blocks().sortByRssi(lvap.addr).first()


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return ProactiveMobilityManager(tenant_id=tenant_id, every=every)
