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

"""Base app class."""

import empower.managers.ranmanager.lvapp as lvapp

from empower.core.service import EService
from empower.core.resourcepool import ResourcePool
from empower.core.cellpool import CellPool

EVERY = 2000


class EApp(EService):
    """Base app class."""

    def __init__(self, service_id, project_id, **kwargs):

        if 'every' not in kwargs:
            kwargs['every'] = EVERY

        super().__init__(service_id=service_id,
                         project_id=project_id,
                         **kwargs)

    def start(self):
        """Start app."""

        # Register default callbacks (LVAPP)
        lvapp.register_callback(lvapp.PT_CLIENT_LEAVE, self._lvap_leave)
        lvapp.register_callback(lvapp.PT_CLIENT_JOIN, self._lvap_join)
        lvapp.register_callback(lvapp.PT_DEVICE_UP, self._wtp_up)
        lvapp.register_callback(lvapp.PT_DEVICE_DOWN, self._wtp_down)

        # start the app
        super().start()

    def stop(self):
        """Stop app."""

        # Unregister default callbacks (LVAPP)
        lvapp.unregister_callback(lvapp.PT_CLIENT_LEAVE, self._lvap_leave)
        lvapp.unregister_callback(lvapp.PT_CLIENT_JOIN, self._lvap_join)
        lvapp.unregister_callback(lvapp.PT_DEVICE_UP, self._wtp_up)
        lvapp.unregister_callback(lvapp.PT_DEVICE_DOWN, self._wtp_down)

        # stop the app
        super().stop()

    def cells(self):
        """Return all available cells in this tenant."""

        # Initialize the Resource Pool
        pool = CellPool()

        # Update the pool with all the available Cells
        for vbs in self.vbses.values():
            for cell in vbs.cells.values():
                pool.append(cell)

        return pool

    def blocks(self):
        """Return all ResourseBlocks in this Tenant."""

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
    def vbses(self):
        """Return the VBSes available to this app."""

        return self.context.vbses

    @property
    def lvaps(self):
        """Return LVAPs in this project."""

        return self.context.lvaps

    @property
    def ueqs(self):
        """Return UEs in this project."""

        return self.context.ueqs

    def _lvap_leave(self, lvap):
        """Check if LVAP is leaving this network."""

        if not self.context.wifi_props:
            return

        if lvap.ssid == self.context.wifi_props.ssid:
            self.lvap_leave(lvap)

    def lvap_leave(self, lvap):
        """Called when an LVAP leavess a network."""

    def _lvap_join(self, lvap):
        """Check if LVAP is leaving this network."""

        if not self.context.wifi_props:
            return

        if lvap.ssid == self.context.wifi_props.ssid:
            self.lvap_join(lvap)

    def lvap_join(self, lvap):
        """Called when an LVAP joins a network."""

    def _wtp_down(self, wtp):
        """Called when a WTP disconnects from the controller."""

        if wtp.addr in self.context.wtps:
            self.wtp_down(wtp)

    def wtp_down(self, wtp):
        """Called when a WTP disconnects from the controller."""

    def _wtp_up(self, wtp):
        """Called when a WTP connects to the controller."""

        if wtp.addr in self.context.wtps:
            self.wtp_up(wtp)

    def wtp_up(self, wtp):
        """Called when a WTP connects to the controller."""

    def _ueq_leave(self, ueq):
        """Check if UE is leaving this network."""

        if not self.context.lte_props:
            return

        if ueq.plmnid == self.context.lte_props.plmnid:
            self.ueq_leave(ueq)

    def ueq_leave(self, ueq):
        """Called when an UE leaves this network."""

    def _ueq_join(self, ueq):
        """Check if UE is joining this network."""

        if not self.context.lte_props:
            return

        if ueq.plmnid == self.context.lte_props.plmnid:
            self.ueq_join(ueq)

    def ueq_join(self, ueq):
        """Called when a UE joins this network."""

    def _vbs_down(self, vbs):
        """Called when a VBS disconnects from the controller."""

        if vbs.addr in self.context.vbses:
            self.vbs_down(vbs)

    def vbs_down(self, vbs):
        """Called when a VBS disconnects from the controller."""

    def _vbs_up(self, vbs):
        """Called when a VBS connects to the controller."""

        if vbs.addr in self.context.vbses:
            self.vbs_up(vbs)

    def vbs_up(self, vbs):
        """Called when a VBS connects to the controller."""
