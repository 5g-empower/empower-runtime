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

"""UE measurements module."""

import uuid

from construct import SBInt16
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import Container
from construct import Struct
from construct import BitStruct
from construct import Padding
from construct import Bit
from construct import Rename
from construct import OptionalGreedyRange

from empower.core.app import EmpowerApp
from empower.core.ue import UE
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import ModulePeriodic
from empower.vbsp import E_TYPE_TRIG
from empower.vbsp import EP_OPERATION_ADD
from empower.vbsp import EP_OPERATION_REM
from empower.vbsp import OPTIONS
from empower.main import RUNTIME


EP_ACT_UE_MEASURE = 0x05

UE_MEASUREMENT_REPORT = Struct("ue_measure_report",
                               UBInt8("type"),
                               UBInt8("version"),
                               Bytes("enbid", 8),
                               UBInt16("cellid"),
                               UBInt32("xid"),
                               BitStruct("flags", Padding(15), Bit("dir")),
                               UBInt32("seq"),
                               UBInt16("length"),
                               UBInt16("action"),
                               UBInt8("opcode"))

UE_MEASURE_REQUEST = Struct("ue_measure_request",
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
                            Rename("options",
                                   OptionalGreedyRange(OPTIONS)))

UE_MEASURE_RESPONSE = Struct("ue_measure_response",
                             Rename("options",
                                    OptionalGreedyRange(OPTIONS)))

RRC_MEASURE_REQUEST = Struct("rrc_measure_request",
                             UBInt16("measure_id"),
                             UBInt16("rnti"),
                             UBInt16("earfcn"),
                             UBInt16("interval"),
                             UBInt16("max_cells"),
                             UBInt16("max_measure"))

RRC_MEASURE_REPORT = Struct("rrc_measure_report",
                            UBInt16("measure_id"),
                            UBInt16("pci"),
                            SBInt16("rsrp"),
                            SBInt16("rsrq"))

EP_RRC_MEASURE_REQUEST = 0x0600
EP_RRC_MEASURE_REPORT = 0x0601

UE_MEASURE_TYPES = {
    EP_RRC_MEASURE_REPORT: RRC_MEASURE_REPORT
}


class UEMeasurements(ModulePeriodic):
    """ UEMurements object. """

    MODULE_NAME = "ue_measurements"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'ue', \
                'rrc_measurements_param']

    def __init__(self):

        super().__init__()

        # parameters
        self._ue = None
        self._rrc_measurements_param = {}

        # stats
        self.rrc_measurements = {}

        # set this for auto-cleanup
        self.vbs = None

    def __eq__(self, other):

        return super().__eq__(other) and self.ue == other.ue and \
            self.rrc_measurements_param == other.rrc_measurements_param

    @property
    def rrc_measurements_param(self):
        """Return rrc_measurements_param."""

        return self._rrc_measurements_param

    @rrc_measurements_param.setter
    def rrc_measurements_param(self, values):
        """Set rrc_measurements_param."""

        self._rrc_measurements_param = {}

        for i, value in enumerate(values):
            self._rrc_measurements_param[i] = {
                "measure_id": i,
                "earfcn": int(value["earfcn"]),
                "interval": int(value["interval"]),
                "max_cells": int(value["max_cells"]),
                "max_measure": int(value["max_measure"])
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
        out['rrc_measurements_param'] = self.rrc_measurements_param
        out['rrc_measurements'] = self.rrc_measurements

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

        # if the vbs exists, first the measurements need to be removed

        if self.vbs:

            msg = Container(options=[], length=UE_MEASUREMENT_REPORT.sizeof())

            for i in self.rrc_measurements_param:

                # RRC measurements
                rrc_measure = Container(measure_id=i,
                                        rnti=0,
                                        earfcn=0,
                                        interval=0,
                                        max_cells=0,
                                        max_measure=0)

                rcc_data = RRC_MEASURE_REQUEST.build(rrc_measure)
                opt_rrc = Container(type=EP_RRC_MEASURE_REQUEST,
                                    length=RRC_MEASURE_REQUEST.sizeof(),
                                    data=rcc_data)

                msg.options.append(opt_rrc)
                msg.length = msg.length + opt_rrc.length + 4

                # Other future measurements like PHY go here.

            self.vbs.connection.send_message(msg,
                                             E_TYPE_TRIG,
                                             EP_ACT_UE_MEASURE,
                                             UE_MEASURE_REQUEST,
                                             cellid=self.ue.cell.pci,
                                             opcode=EP_OPERATION_REM,
                                             xid=self.module_id)

        self.rrc_measurements = {}

        self.vbs = self.ue.vbs

        msg = Container(options=[], length=UE_MEASUREMENT_REPORT.sizeof())

        for i, measure in self.rrc_measurements_param.items():

            # RRC measurements
            rrc_measure = Container(measure_id=i,
                                    rnti=self.ue.rnti,
                                    earfcn=measure["earfcn"],
                                    interval=measure["interval"],
                                    max_cells=measure["max_cells"],
                                    max_measure=measure["max_measure"])

            rcc_data = RRC_MEASURE_REQUEST.build(rrc_measure)
            opt_rrc = Container(type=EP_RRC_MEASURE_REQUEST,
                                length=RRC_MEASURE_REQUEST.sizeof(),
                                data=rcc_data)

            msg.options.append(opt_rrc)
            msg.length = msg.length + opt_rrc.length + 4
            # Other future measurements like PHY go here.

        self.vbs.connection.send_message(msg,
                                         E_TYPE_TRIG,
                                         EP_ACT_UE_MEASURE,
                                         UE_MEASURE_REQUEST,
                                         cellid=self.ue.cell.pci,
                                         opcode=EP_OPERATION_ADD,
                                         xid=self.module_id)


    def handle_response(self, response):
        """Handle an incoming UE_MEASUREMENTS message.
        Args:
            response, a UE_MEASUREMENTS message
        Returns:
            None
        """

        for raw_entry in response.options:

            if raw_entry.type not in UE_MEASURE_TYPES:
                self.log.warning("Unknown options %u", raw_entry)
                continue

            prop = UE_MEASURE_TYPES[raw_entry.type].name
            option = UE_MEASURE_TYPES[raw_entry.type].parse(raw_entry.data)

            self.log.warning("Processing options %s", prop)

            if raw_entry.type == EP_RRC_MEASURE_REPORT:

                # save measurements in this object
                if option.measure_id not in self.rrc_measurements:
                    self.rrc_measurements[option.measure_id] = {}

                self.rrc_measurements[option.measure_id][option.pci] = {
                    "measure_id": option.measure_id,
                    "rsrp": option.rsrp,
                    "rsrq": option.rsrq
                }

                # check if this measurement refers to a cell that is in this tenant
                earfcn = self.rrc_measurements_param[option.measure_id]["earfcn"]

                for vbs in RUNTIME.tenants[self.tenant_id].vbses.values():

                    for cell in vbs.cells.values():

                        if cell.pci == option.pci and cell.dl_earfcn == earfcn:

                            if self.ue.ue_id not in cell.ue_measurements:
                                cell.ue_measurements[self.ue.ue_id] = {}

                            if 'rrc_measurements' \
                                not in cell.ue_measurements[self.ue.ue_id]:
                                cell.ue_measurements[self.ue.ue_id] \
                                    ['rrc_measurements'] = {}

                            cell.ue_measurements[self.ue.ue_id] \
                                ['rrc_measurements'] = {
                                    "rsrp": option.rsrp,
                                    "rsrq": option.rsrq
                                }

                            if vbs.addr not in self.ue.ue_measurements:
                                self.ue.ue_measurements[vbs.addr] = {}

                            if cell.pci not in self.ue.ue_measurements[vbs.addr]:
                                self.ue.ue_measurements[vbs.addr][cell.pci] = {}

                            self.ue.ue_measurements[vbs.addr][cell.pci] \
                                ['rrc_measurements'] = {
                                    "rsrp": option.rsrp,
                                    "rsrq": option.rsrq
                                }

                # call callback
                self.handle_callback(self)

class UEMeasurementsWorker(ModuleVBSPWorker):
    """ Counter worker. """

    pass


def ue_measurements(**kwargs):
    """Create a new module."""

    module = UEMeasurementsWorker.__module__
    return RUNTIME.components[module].add_module(**kwargs)


def bound_ue_measurements(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return ue_measurements(**kwargs)


setattr(EmpowerApp, UEMeasurements.MODULE_NAME, bound_ue_measurements)


def launch():
    """ Initialize the module. """

    return UEMeasurementsWorker(UEMeasurements,
                                EP_ACT_UE_MEASURE,
                                UE_MEASURE_RESPONSE)
