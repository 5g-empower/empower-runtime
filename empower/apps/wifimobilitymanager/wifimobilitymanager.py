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

"""A simple Wi-Fi mobility manager."""

from empower.core.app import EApp
from empower.core.app import EVERY


class WiFiMobilityManager(EApp):
    """A simple Wi-Fi mobility manager.

    This app will peridodically handover every LVAP in the network to the
    interface with the highest RSSI.

    Parameters:
        service_id: the application id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)
        every: the loop period in ms (optional, default 2000ms)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.wifimobilitymanager.wifimobilitymanager",
            "params": {
                "every": 2000
            }
        }
    """

    def loop(self):
        """Periodic job."""

        for lvap in self.lvaps.values():
            lvap.blocks = self.blocks().sort_by_rssi(lvap.addr).first()


def launch(service_id, project_id, every=EVERY):
    """ Initialize the module. """

    return WiFiMobilityManager(service_id=service_id,
                               project_id=project_id,
                               every=every)
