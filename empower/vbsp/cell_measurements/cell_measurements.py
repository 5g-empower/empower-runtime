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

"""MAC Reports module."""

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
from empower.datatypes.etheraddress import EtherAddress
from empower.core.cellpool import Cell
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import ModuleScheduled
from empower.vbsp import E_TYPE_SCHED
from empower.vbsp import EP_OPERATION_ADD
from empower.vbsp import OPTIONS
from empower.main import RUNTIME


EP_ACT_CELL_MEASURE = 0x06

CELL_MEASURE_REPORT = Struct("cell_measure_report",
                             UBInt8("type"),
                             UBInt8("version"),
                             Bytes("enbid", 8),
                             UBInt16("cellid"),
                             UBInt32("xid"),
                             BitStruct("flags", Padding(15), Bit("dir")),
                             UBInt32("seq"),
                             UBInt16("length"),
                             UBInt16("action"),
                             UBInt32("interval"),
                             UBInt8("opcode"))

CELL_MEASURE_REQUEST = Struct("cell_measure_request",
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
                              UBInt32("interval"),
                              Rename("options",
                                     OptionalGreedyRange(OPTIONS)))

CELL_MEASURE_RESPONSE = Struct("cell_measure_response",
                               Rename("options",
                                      OptionalGreedyRange(OPTIONS)))

MAC_PRBS_REQUEST = Struct("mac_prbs_request")

MAC_PRBS_REPORT = Struct("mac_prbs_report",
                         UBInt8("dl_prbs_total"),
                         UBInt32("dl_prbs_used"),
                         UBInt8("ul_prbs_total"),
                         UBInt32("ul_prbs_used"))

EP_MAC_PRBS_REQUEST = 0x0101
EP_MAC_PRBS_REPORT = 0x0102

CELL_MEASURE_TYPES = {
    EP_MAC_PRBS_REPORT: MAC_PRBS_REPORT
}


class CellMeasurements(ModuleScheduled):
    """ CellMeasurements object. """

    MODULE_NAME = "cell_measurements"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'cell', 'interval']

    def __init__(self):

        super().__init__()

        # parameters
        self._cell = None
        self._interval = None

        # stats
        self.mac_prbs_measurements = {}

        # set this for auto-cleanup
        self.vbs = None

    def __eq__(self, other):

        return super().__eq__(other) and self.cell == other.cell and \
            self.cell == other.cell and self.interval == other.interval

    @property
    def cell(self):
        """Return the cell."""

        return self._cell

    @cell.setter
    def cell(self, value):

        if isinstance(value, Cell):
            self._cell = value

        elif isinstance(value, dict):

            if 'pci' not in value:
                raise ValueError("Missing field: cellid")

            if 'vbs' not in value:
                raise ValueError("Missing field: vbs")

            vbs = RUNTIME.vbses[EtherAddress(value['vbs'])]
            pci = int(value['pci'])

            self._cell = vbs.get_cell(pci)

            if not self._cell:
                raise ValueError("Invalid pci %u" % pci)

        else:

            raise Exception("Invalid cell value %s" % value)

    @property
    def interval(self):
        """Return the interval."""

        return self._interval

    @interval.setter
    def interval(self, value):
        """Set the interval."""

        self._interval = int(value)

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['cell'] = self.cell
        out['interval'] = self.interval
        out['mac_prbs_measurements'] = self.mac_prbs_measurements

        return out

    def run_once(self):
        """Send out rate request."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.cell.vbs.addr not in tenant.vbses:
            self.log.info("VBS %s not found", self.cell.vbs.addr)
            self.unload()
            return

        self.vbs = self.cell.vbs

        msg = Container(interval=self.interval, options=[])

        # MAC RBGs
        mac_rbgs = Container()
        mac_rbgs_data = MAC_PRBS_REQUEST.build(mac_rbgs)
        opt_mac_rbgs = Container(type=EP_MAC_PRBS_REQUEST,
                                 length=MAC_PRBS_REQUEST.sizeof(),
                                 data=mac_rbgs_data)

        # Other future measurements go here

        msg.options.append(opt_mac_rbgs)

        msg.length = CELL_MEASURE_REPORT.sizeof() + \
                     opt_mac_rbgs.length + 4

        self.vbs.connection.send_message(msg,
                                         E_TYPE_SCHED,
                                         EP_ACT_CELL_MEASURE,
                                         CELL_MEASURE_REQUEST,
                                         cellid=self.cell.pci,
                                         xid=self.module_id,
                                         opcode=EP_OPERATION_ADD)

    def handle_response(self, response):
        """Handle an incoming CELL_MEASURE_RESPONSE message.
        Args:
            response, a CELL_MEASURE_RESPONSE message
        Returns:
            None
        """

        for raw_entry in response.options:

            if raw_entry.type not in CELL_MEASURE_TYPES:
                self.log.warning("Unknown options %u", raw_entry)
                continue

            prop = CELL_MEASURE_TYPES[raw_entry.type].name
            option = CELL_MEASURE_TYPES[raw_entry.type].parse(raw_entry.data)

            self.log.warning("Processing options %s", prop)

            if raw_entry.type == EP_MAC_PRBS_REPORT:

                # save measurements in this object

                dl_prbs_last = self.mac_prbs_measurements['dl_prbs_last'] \
                    if 'dl_prbs_last' in self.mac_prbs_measurements else 0

                ul_prbs_last = self.mac_prbs_measurements['ul_prbs_last'] \
                    if 'ul_prbs_last' in self.mac_prbs_measurements else 0

                self.mac_prbs_measurements = {
                    'dl_prbs_total': option.dl_prbs_total,
                    'dl_prbs_used': option.dl_prbs_used,
                    'dl_prbs_last': option.dl_prbs_used - dl_prbs_last,
                    'dl_util_last': float(option.dl_prbs_used - dl_prbs_last) / \
                                    (option.dl_prbs_total * self.interval),
                    'ul_prbs_total': option.ul_prbs_total,
                    'ul_prbs_used': option.ul_prbs_used,
                    'ul_prbs_last': option.ul_prbs_used - ul_prbs_last,
                    'ul_util_last': float(option.ul_prbs_used - ul_prbs_last) / \
                                    (option.ul_prbs_total * self.interval)
                }

        self.cell.cell_measurements['mac_prbs_report'] = \
            self.mac_prbs_measurements

        # call callback
        self.handle_callback(self)


class CellMeasurementsWorker(ModuleVBSPWorker):
    """ Counter worker. """

    pass


def cell_measurements(**kwargs):
    """Create a new module."""

    module = CellMeasurementsWorker.__module__
    return RUNTIME.components[module].add_module(**kwargs)


def bound_cell_measurements(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return cell_measurements(**kwargs)


setattr(EmpowerApp, CellMeasurements.MODULE_NAME, bound_cell_measurements)


def launch():
    """ Initialize the module. """

    return CellMeasurementsWorker(CellMeasurements, EP_ACT_CELL_MEASURE, \
            CELL_MEASURE_RESPONSE)
