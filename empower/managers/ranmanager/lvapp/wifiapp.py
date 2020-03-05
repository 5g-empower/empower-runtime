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

"""Base Wi-Fi App class."""

from empower.core.app import EApp

import empower.managers.ranmanager.lvapp as lvapp

from empower.managers.ranmanager.lvapp.resourcepool import ResourcePool

EVERY = 2000


class EWiFiApp(EApp):
    """Base Wi-Fi App class."""

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
        """Return the WTPs available to this app."""

        return self.context.wtps

    @property
    def lvaps(self):
        """Return the LVAPs available to this app."""

        return self.context.lvaps

    def handle_client_leave(self, lvap):
        """Called when a client leaves a network (no check on project)."""

        if not self.context.wifi_props:
            return

        if lvap.ssid == self.context.wifi_props.ssid:
            self.handle_lvap_leave(lvap)

    def handle_lvap_leave(self, lvap):
        """Called when an LVAP leaves a network."""

    def handle_client_join(self, lvap):
        """Called when a client joins a network (no check on project)."""

        if not self.context.wifi_props:
            return

        if lvap.ssid == self.context.wifi_props.ssid:
            self.handle_lvap_join(lvap)

    def handle_lvap_join(self, lvap):
        """Called when an LVAP joins a network."""

    def handle_device_down(self, wtp):
        """Called when a device disconnects from the controller."""

        self.handle_wtp_down(wtp)

    def handle_wtp_down(self, wtp):
        """Called when a wtp disconnects to the controller."""

    def handle_device_up(self, wtp):
        """Called when a device connects to the controller."""

        self.handle_wtp_up(wtp)

    def handle_wtp_up(self, wtp):
        """Called when a wtp connects to the controller."""
