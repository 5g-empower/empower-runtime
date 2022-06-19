#!/usr/bin/env python3
#
# Copyright (c) 2022 Roberto Riggio
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

"""Static rates."""

from empower.managers.ranmanager.lvapp.wifiapp import EWiFiApp
from empower_core.app import EVERY
from empower_core.etheraddress import EtherAddress
from empower.managers.ranmanager.lvapp.txpolicy import TxPolicy
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_DMS
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_LEGACY
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_DMS_H
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_LEGACY_H
from empower.managers.ranmanager.lvapp.resourcepool import BT_HT20


class Rates(EWiFiApp):
    """Static rates.

    Parameters:
        service_id: the application id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)
        every: the loop period in ms (optional, default 2000ms)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.rates.rates",
            "params": {
                "every": 2000
            }
        }
    """

    def loop(self):
        """Periodic loop."""

        for lvap in self.lvaps.values():
            lvap.txp.ht_mcs = [0,1,2,3]

def launch(context, service_id, every=EVERY):
    """ Initialize the module. """

    return Rates(context=context, service_id=service_id, every=every)
