#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""RRC Statistics Poller Apps."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class RRCMeasurementsPoller(EmpowerApp):
    """RRC Measurements Poller Apps.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.pollers.rrcpoller \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.uejoin(callback=self.ue_join_callback)

    def ue_join_callback(self, ue):
        """ New UE. """

        measurements = \
            [{"earfcn": ue.cell.DL_earfcn, "interval": 2000, "max_cells": 2,
              "max_meas": 2},
             {"earfcn": 2600, "interval": 1000, "max_cells": 5, "max_meas": 5}]

        print(ue.ue_id)

        self.rrc_measurements(ue_id=ue.ue_id,
                              measurements=measurements,
                              callback=self.rrc_measurements_callback)

    def rrc_measurements_callback(self, rrc):
        """ New measurements available. """

        self.log.info("New rrc measurements received from %s" % rrc.ue_id)


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return RRCMeasurementsPoller(tenant_id=tenant_id, every=every)
