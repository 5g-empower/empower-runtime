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
from empower.core.lvap import PROCESS_REMOVING
from empower.main import RUNTIME
from empower.vbsp.rrc_measurements.rrc_measurements import RRCMeasurementsWorker


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


    def delete_ue_meas_worker(self, ue):
        """ Delete the worker for the UE measurements. """

        worker = RUNTIME.components[RRCMeasurementsWorker.__module__]

        for module_id in list(worker.modules.keys()):
            ue_meas_mod = worker.modules[module_id]
            if ue == ue_meas_mod.ue:
                worker.remove_module(module_id)


    def update_rrc_measurements(self, ue):
        """ Update the measurements for the updated RNTI. """

        measurements = \
            [{"earfcn": ue.cell.dl_earfcn,
              "interval": 2000,
              "max_cells": 2,
              "max_meas": 2}]

        self.rrc_measurements(ue=ue, measurements=measurements)


    def loop(self):
        """ Periodic job. """

        for ueq in self.ues():
            for cell in self.cells():
                if ueq.ue_id not in cell.rrc_measurements:
                    continue
                print("Cell %s UE %s -> RSRQ %d" % (cell.vbs.addr, ueq.ue_id, cell.rrc_measurements[ueq.ue_id]['rsrq']))

            target_cell = self.cells().sort_by_rsrq(ueq.ue_id).first()

            if target_cell == ueq.cell:
                continue

            if ueq.ue_id not in ueq.cell.rrc_measurements:
                continue

            if ueq.state == PROCESS_REMOVING:
                continue

            print("Handover from VBS %s to VBS %s for UE %s" %(ueq.cell, target_cell, ueq.ue_id))
            self.delete_ue_meas_worker(ueq)
            self.update_rrc_measurements(ueq)
            ueq.cell = target_cell


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return MobilityManager(tenant_id=tenant_id, every=every)
