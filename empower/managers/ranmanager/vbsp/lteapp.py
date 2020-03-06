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

import empower.managers.ranmanager.vbsp as vbsp

from empower.managers.ranmanager.vbsp.cellpool import CellPool


class ELTEApp(EApp):
    """Base LTE App class."""

    MODULES = [vbsp]

    def cells(self):
        """Return the Cells available to this app."""

        # Initialize the Cell Pool
        pool = CellPool()

        # Update the pool with all the available Cells
        for vbs in self.vbses.values():
            for cell in vbs.cells.values():
                pool.append(cell)

        return pool

    @property
    def vbses(self):
        """Return the VBSes available to this app."""

        return self.context.vbses

    @property
    def ues(self):
        """Return the UEs available to this app."""

        return self.context.ueqs

    def handle_client_leave(self, ueq):
        """Called when a client leaves a network."""

        if not self.context.lte_props:
            return

        if ueq.plmnid == self.context.lte_props.plmnid:
            self.handle_ue_leave(ueq)

    def handle_ue_leave(self, ueq):
        """Called when a UE leaves a network."""

    def handle_client_join(self, ueq):
        """Called when a client joins a network."""

        if not self.context.lte_props:
            return

        if ueq.plmnid == self.context.lte_props.plmnid:
            self.handle_ue_join(ueq)

    def handle_ue_join(self, ueq):
        """Called when a UE joins a network."""

    def handle_device_down(self, vbs):
        """Called when a device disconnects from the controller."""

        self.handle_vbs_down(vbs)

    def handle_vbs_down(self, vbs):
        """Called when a vbs disconnects to the controller."""

    def handle_device_up(self, vbs):
        """Called when a device connects to the controller."""

        self.handle_vbs_up(vbs)

    def handle_vbs_up(self, vbs):
        """Called when a vbs connects to the controller."""
