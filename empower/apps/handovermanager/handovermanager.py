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
from empower.core.cellpool import CellPool


class MobilityManager(EmpowerApp):
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

        self.rrc_measurements(ue=ue, measurements=measurements)

    def cells(self):

        # Initialize the Resource Pool
        pool = CellPool()

        # Update the pool with all the a
        # Initialize the Resource Poolvailable ResourseBlocks
        for vbs in self.vbses():
            for cell in vbs.cells.values():
                pool.append(cell)

        return pool

    def loop(self):
        """ Periodic job. """

        for ue in self.ues():
        	ue.cell = self.cells().sort_by_rsrp(ue.ue_id).first()


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return MobilityManager(tenant_id=tenant_id, every=every)
