#!/usr/bin/env python3
#
# Copyright (c) 2018 Roberto Riggio
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

"""Events Apps."""

from empower.core.app import EmpowerApp


class EventsApp(EmpowerApp):
    """Events App.

    Command Line Parameters:

        tenant_id: tenant id

    Example:

        ./empower-runtime.py apps.events.events \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def lvap_join(self, lvap):
        """Called when an LVAP joins a tenant."""

        self.log.info("LVAP %s joined %s!", lvap.addr, lvap.ssid)

    def lvap_leave(self, lvap):
        """Called when an LVAP leaves a tenant."""

        self.log.info("LVAP %s left %s!", lvap.addr, lvap.ssid)

    def vbs_down(self, vbs):
        """Called when a VBS disconnects to the controller."""

        self.log.info("VBS %s disconnected!", vbs.addr)

    def vbs_up(self, vbs):
        """Called when a VBS connects from the controller."""

        self.log.info("VBS %s connected!", vbs.addr)

    def wtp_down(self, wtp):
        """Called when a VBS disconnects to the controller."""

        self.log.info("WTP %s disconnected!", wtp.addr)

    def wtp_up(self, wtp):
        """Called when a WTP connects from the controller."""

        self.log.info("WTP %s connected!", wtp.addr)

    def cpp_down(self, cpp):
        """Called when a CPP disconnects to the controller."""

        self.log.info("CPP %s disconnected!", cpp.addr)

    def cpp_up(self, cpp):
        """Called when a VBS connects from the controller."""

        self.log.info("CPP %s connected!", cpp.addr)


def launch(tenant_id):
    """Initialize the app."""

    return EventsApp(tenant_id=tenant_id)
