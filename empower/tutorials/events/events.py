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

"""Tutorial: Events."""

from empower.core.app import EApp


class TutorialEvents(EApp):
    """Tutorial: Events.

    Parameters:
        service_id: the service id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.events.events",
        }
    """

    def lvap_join(self, lvap):
        """Called when an LVAP joins a network."""

        self.log.info("LVAP %s joined %s!", lvap.addr, lvap.ssid)

    def lvap_leave(self, lvap):
        """Called when an LVAP leaves a network."""

        self.log.info("LVAP %s left %s!", lvap.addr, lvap.ssid)

    def wtp_down(self, wtp):
        """Called when a VBS disconnects to the controller."""

        self.log.info("WTP %s disconnected!", wtp.addr)

    def wtp_up(self, wtp):
        """Called when a WTP connects from the controller."""

        self.log.info("WTP %s connected!", wtp.addr)


def launch(service_id, project_id, every=-1):
    """Initialize the app."""

    return TutorialEvents(service_id=service_id,
                          project_id=project_id,
                          every=every)
