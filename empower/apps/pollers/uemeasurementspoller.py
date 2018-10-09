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

"""UE Statistics Poller Apps."""

from empower.core.app import EmpowerApp


class UEMeasurementsPoller(EmpowerApp):
    """UE Measurements Poller Apps.

    Command Line Parameters:
        tenant_id: tenant id

    Example:
        ./empower-runtime.py apps.pollers.uemeasurementspoller \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def ue_join(self, ue):
        """ New UE. """

        measurements = \
            [{"earfcn": ue.cell.dl_earfcn,
              "interval": 2000,
              "max_cells": 2,
              "max_meas": 2}]

        self.ue_measurements(ue=ue, measurements=measurements)


def launch(tenant_id):
    """ Initialize the module. """

    return UEMeasurementsPoller(tenant_id=tenant_id)
