#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""Base Wi-Fi Worker class."""

from empower.core.worker import EWorker

import empower.managers.ranmanager.lvapp as lvapp

from empower.core.launcher import srv_or_die
from empower.managers.ranmanager.lvapp.resourcepool import ResourcePool

EVERY = 2000


class EWiFiWorker(EWorker):
    """Base Wi-Fi Worker class."""

    MODULES = [lvapp]

    def blocks(self):
        """Return the ResourseBlocks available to this app."""

        # Initialize the Resource Pool
        pool = ResourcePool()

        # Update the pool with all the available ResourseBlocks
        for wtp in self.wtps.values():
            for block in wtp.blocks.values():
                pool.append(block)

        return pool

    @property
    def wtps(self):
        """Return the WTPs."""

        return srv_or_die("lvappmanager").devices

    @property
    def lvaps(self):
        """Return the LVAPs."""

        return srv_or_die("lvappmanager").lvaps

    @property
    def vaps(self):
        """Return the VAPs."""

        return srv_or_die("lvappmanager").vaps

    def handle_client_leave(self, lvap):
        """Called when a client leaves a network (no check on project)."""

    def handle_client_join(self, lvap):
        """Called when a client joins a network (no check on project)."""

    def handle_device_down(self, wtp):
        """Called when a WTP disconnects from the controller."""

    def handle_device_up(self, wtp):
        """Called when a WTP connects to the controller."""
