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


class EWApp(EApp):
    """Base Wi-Fi App class."""

    def start(self):
        """Start app."""

        # register callbacks
        vbsp.register_callback(vbsp.PT_CLIENT_LEAVE, self._ue_leave)
        vbsp.register_callback(vbsp.PT_CLIENT_JOIN, self._ue_join)
        vbsp.register_callback(vbsp.PT_DEVICE_UP, self._vbs_up)
        vbsp.register_callback(vbsp.PT_DEVICE_DOWN, self._vbs_down)

        # start the app
        super().start()

    def stop(self):
        """Stop app."""

        # unregister callbacks
        vbsp.unregister_callback(vbsp.PT_CLIENT_LEAVE, self._ue_leave)
        vbsp.unregister_callback(vbsp.PT_CLIENT_JOIN, self._ue_join)
        vbsp.unregister_callback(vbsp.PT_DEVICE_UP, self._vbs_up)
        vbsp.unregister_callback(vbsp.PT_DEVICE_DOWN, self._vbs_down)

        # stop the app
        super().stop()

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

    def _ue_leave(self, ueq):
        """Called when a UE leave a network."""

        if not self.context.lte_props:
            return

        if ueq.plmnid == self.context.lte_props.plmnid:
            self.ue_leave(ueq)

    def ue_leave(self, ueq):
        """Called when a UE leavess a network."""

    def _ue_join(self, ueq):
        """Called when a UE joins a network."""

        if not self.context.lte_props:
            return

        if ueq.plmnid == self.context.lte_props.plmnid:
            self.ue_join(ueq)

    def ue_join(self, ueq):
        """Called when an LVAP joins a network."""

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
        """Called when a vbs connects to the controller."""
