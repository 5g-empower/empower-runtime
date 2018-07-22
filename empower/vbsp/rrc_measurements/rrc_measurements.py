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

"""RRC measurements module."""

import uuid

from construct import SBInt16
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import Container
from construct import Struct
from construct import Array
from construct import BitStruct
from construct import Padding
from construct import Bit

from empower.core.app import EmpowerApp
from empower.core.ue import UE
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import ModulePeriodic
from empower.vbsp import E_TYPE_TRIG
from empower.vbsp import EP_OPERATION_ADD
from empower.vbsp import EP_OPERATION_REM
from empower.main import RUNTIME


EP_ACT_RRC_MEASUREMENT = 0x05

RRC_REQUEST = Struct("rrc_request",
                     UBInt8("type"),
                     UBInt8("version"),
                     Bytes("enbid", 8),
                     UBInt16("cellid"),
                     UBInt32("xid"),
                     BitStruct("flags", Padding(15), Bit("dir")),
                     UBInt32("seq"),
                     UBInt16("length"),
                     UBInt16("action"),
                     UBInt8("opcode"),
                     UBInt8("meas_id"),
                     UBInt16("rnti"),
                     UBInt16("earfcn"),
                     UBInt16("interval"),
                     UBInt16("max_cells"),
                     UBInt16("max_meas"))

RRC_ENTRY = Struct("rrc_entries",
                   UBInt8("meas_id"),
                   UBInt16("pci"),
                   SBInt16("rsrp"),
                   SBInt16("rsrq"))

RRC_RESPONSE = Struct("rrc_response",
                      UBInt32("nof_meas"),
                      Array(lambda ctx: ctx.nof_meas, RRC_ENTRY))


class RRCMeasurements(ModulePeriodic):
    """ LVAPStats object. """

    MODULE_NAME = "rrc_measurements"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'ue', 'measurements']

    def __init__(self):

        super().__init__()

        # parameters
        self._ue = None
        self._measurements = {}

        # stats
        self.results = {}

        # set this for auto-cleanup
        self.vbs = None

    def __eq__(self, other):

        return super().__eq__(other) and self.ue == other.ue and \
            self.measurements == other.measurements

    @property
    def measurements(self):
        """Return measurements."""

        return self._measurements

    @measurements.setter
    def measurements(self, value):
        """Set measurements."""

        self._measurements = {}

        for i in range(0, len(value)):

            meas = value[i]

            self._measurements[i] = {
                "meas_id": i,
                "earfcn": int(meas["earfcn"]),
                "interval": int(meas["interval"]),
                "max_cells": int(meas["max_cells"]),
                "max_meas": int(meas["max_meas"])
            }

    @property
    def ue(self):
        """Return the ue."""

        return self._ue

    @ue.setter
    def ue(self, value):
        """Set UE."""

        if isinstance(value, UE):
            self._ue = value

        elif isinstance(value, str):

            self._ue = RUNTIME.ues[uuid.UUID(str(value))]

        else:

            raise Exception("Invalid ue value %s" % value)

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['ue'] = self.ue
        out['measurements'] = self.measurements
        out['results'] = self.results

        return out

    def run_once(self):
        """Send out rate request."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.ue.ue_id not in tenant.ues:
            self.log.info("UE %u not found", self.ue.ue_id)
            self.unload()
            return

        if not self.ue.vbs or not self.ue.vbs.is_online():
            self.log.info("VBS %s not connected", self.ue.vbs.addr)
            self.unload()
            return

        # if the vbs did not change since last time then return
        if self.vbs == self.ue.vbs:
            return

        if self.vbs:

            for i in self.measurements:
                msg = Container(meas_id=i,
                                rnti=0,
                                earfcn=0,
                                interval=0,
                                max_cells=0,
                                max_meas=0)

                self.vbs.connection.send_message(msg,
                                                 E_TYPE_TRIG,
                                                 EP_ACT_RRC_MEASUREMENT,
                                                 RRC_REQUEST,
                                                 cellid=self.ue.cell.pci,
                                                 xid=self.module_id,
                                                 opcode=EP_OPERATION_REM)

        self.results = {}

        self.vbs = self.ue.vbs

        for i in self.measurements:

            measurement = self.measurements[i]

            msg = Container(meas_id=i,
                            rnti=self.ue.rnti,
                            earfcn=measurement["earfcn"],
                            interval=measurement["interval"],
                            max_cells=measurement["max_cells"],
                            max_meas=measurement["max_meas"])

            self.vbs.connection.send_message(msg,
                                             E_TYPE_TRIG,
                                             EP_ACT_RRC_MEASUREMENT,
                                             RRC_REQUEST,
                                             cellid=self.ue.cell.pci,
                                             xid=self.module_id,
                                             opcode=EP_OPERATION_ADD)

    def handle_response(self, response):
        """Handle an incoming RRC_MEASUREMENTS message.
        Args:
            meas, a RRC_MEASUREMENTS message
        Returns:
            None
        """

        for entry in response.rrc_entries:

            # save measurements in this object
            if entry.meas_id not in self.results:
                self.results[entry.meas_id] = {}

            self.results[entry.meas_id][entry.pci] = {
                "meas_id": entry.meas_id,
                "pci": entry.pci,
                "rsrp": entry.rsrp,
                "rsrq": entry.rsrq
            }

            # check if this measurement refers to a cell that is in this tenant
            earfcn = self.measurements[entry.meas_id]["earfcn"]

            for vbs in RUNTIME.tenants[self.tenant_id].vbses.values():
                for cell in vbs.cells.values():
                    if cell.pci == entry.pci and cell.dl_earfcn == earfcn:
                        cell.rrc_measurements[self.ue.ue_id] = {
                            "rsrp": entry.rsrp,
                            "rsrq": entry.rsrq
                        }

        # call callback
        self.handle_callback(self)


class RRCMeasurementsWorker(ModuleVBSPWorker):
    """ Counter worker. """

    pass


def rrc_measurements(**kwargs):
    """Create a new module."""

    module = RRCMeasurementsWorker.__module__
    return RUNTIME.components[module].add_module(**kwargs)


def bound_rrc_measurements(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return rrc_measurements(**kwargs)


setattr(EmpowerApp, RRCMeasurements.MODULE_NAME, bound_rrc_measurements)


def launch():
    """ Initialize the module. """

    return RRCMeasurementsWorker(RRCMeasurements,
                                 EP_ACT_RRC_MEASUREMENT,
                                 RRC_RESPONSE)
