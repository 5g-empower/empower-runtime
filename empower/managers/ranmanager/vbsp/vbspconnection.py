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

"""VBSP Connection."""

from empower.managers.ranmanager.ranconnection import RANConnection


class VBSPConnection(RANConnection):
    """A persistent connection to a VBS."""

    def on_disconnect(self):
        """Handle protocol-specific device disconnection."""

        # Remove hosted UEQs
        ueqs = [ueq for ueq in self.manager.ueqs.values()
                if ueq.vbs.addr == self.device.addr]

        for ueq in list(ueqs):
            del self.manager.ueqs[ueq.addr]

    def _handle_caps_response(self, caps):
        """Handle an incoming CAPS message."""

        # parse cells
        print(caps)

        # set state to online
        super()._handle_caps_response(caps)
