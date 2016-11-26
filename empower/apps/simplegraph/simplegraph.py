#!/usr/bin/env python3
#
# Copyright (c) 2016 Supreeth Herle
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

"""Simple graph app."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.events.uejoin import uejoin

from empower.main import RUNTIME

MEAS_REQ = {
    "rat_type": "EUTRA",
    "cell_to_measure": [],
    "blacklist_cells": [],
    "bandwidth": 50,
    "carrier_freq": 6400,
    "report_type": "periodical_ref_signal",
    "threshold1": {
        "type": "RSRP",
        "value": 20
    },
    "threshold2": {
        "type": "RSRP",
        "value": 50
    },
    "report_interval": 10,
    "trigger_quantity": "RSRP",
    "num_of_reports": "infinite",
    "max_report_cells": 3,
    "a3_offset": 5
}


class SimpleGraph(EmpowerApp):
    """Signal strength visulization app.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.simplegraph.simplegraph \
            --tenant_id=d18a6e8f-699b-4280-ab6f-435bd00e1c90
    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.uejoin(callback=self.ue_join_callback)

    def ue_join_callback(self, ue):
        """Reconfigure RRC measurement on UE join."""

        ue.vbs_rrc_stats(meas_req=MEAS_REQ, callback=self.rrc_stats_callback)

    def rrc_stats_callback(self, meas_resp):
        """RRC measurement callback."""

        pass


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return SimpleGraph(tenant_id=tenant_id, every=DEFAULT_PERIOD)
