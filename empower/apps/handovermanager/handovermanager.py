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

"""A basic LTE handover manager."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class HandoverManager(EmpowerApp):
    """A basic LTE handover manager.

    This app move every UE in the tenant to the cell with the best rsrp.

    Command Line Parameters:
        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:
        ./empower-runtime.py apps.handovermanager.handovermanager \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26
    """

    def ue_join(self, ue):
        """ New UE. """

        measurements = \
            [{"earfcn": ue.cell.dl_earfcn,
              "interval": 2000,
              "max_cells": 2,
              "max_meas": 2}]

        self.ue_measurements(ue=ue, measurements=measurements)

    def loop(self):
        """ Periodic job. """

        for ueq in self.ues():
            ueq.cell = self.cells().sort_by_rsrq(ueq.ue_id).first()


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return HandoverManager(tenant_id=tenant_id, every=every)
