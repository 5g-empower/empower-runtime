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
from construct import Sequence
from construct import Container
from construct import Struct
from construct import Array
from construct import BitStruct
from construct import Padding
from construct import Bit

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.core.vbs import Cell
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import ModuleTrigger
from empower.vbsp import PT_VERSION
from empower.vbsp import E_TYPE_TRIG
from empower.vbsp import EP_DIR_REQUEST
from empower.vbsp import EP_OPERATION_ADD

from empower.main import RUNTIME


EP_ACT_MAC_REPORTS = 0x06

MAC_REPORTS_REQ = Struct("mac_reports_req",
                         UBInt8("type"),
                         UBInt8("version"),
                         UBInt32("enbid"),
                         UBInt16("cellid"),
                         UBInt32("modid"),
                         UBInt16("length"),
                         UBInt32("seq"),
                         UBInt8("action"),
                         UBInt8("dir"),
                         UBInt8("op"),
                         UBInt16("deadline"))

MAC_REPORTS_RESP = Struct("mac_reports_resp",
                          UBInt8("DL_prbs_total"),
                          UBInt8("DL_prbs_in_use"),
                          UBInt16("DL_prbs_avg"),
                          UBInt8("UL_prbs_total"),
                          UBInt8("UL_prbs_in_use"),
                          UBInt16("UL_prbs_avg"))


class MACReports(ModuleTrigger):
    """ LVAPStats object. """

    MODULE_NAME = "mac_reports"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'cell', 'deadline']

    def __init__(self):

        super().__init__()

        # parameters
        self._cell = None
        self._deadline = None

        # stats
        self.results = {}

        # set this for auto-cleanup
        self.vbs = None

    def __eq__(self, other):

        return super().__eq__(other) and self.cell == other.cell and \
            self.cell == other.cell and self.deadline == other.deadline

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

            self._cell = None

            for cell in vbs.cells:
                if cell.pci == pci:
                    self._cell = cell

            if not self._cell:
                raise ValueError("Invalid pci %u", pci)

    @property
    def deadline(self):
        """Return the deadline."""

        return self._deadline

    @deadline.setter
    def deadline(self, value):
        """Set the deadline."""

        self._deadline = int(value)

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['cell'] = self.cell
        out['deadline'] = self.deadline
        out['results'] = self.results

        return out

    def run_once(self):
        """Send out rate request."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.cell.vbs.addr not in tenant.vbses:
            self.log.info("VBS %s not found", self.self.cell.vbs.addr)
            self.unload()
            return

        self.vbs = self.cell.vbs

        mac_reports_req = Container(type=E_TYPE_TRIG,
                                    cellid=self.cell.pci,
                                    modid=self.module_id,
                                    length=MAC_REPORTS_REQ.sizeof(),
                                    action=EP_ACT_MAC_REPORTS,
                                    dir=EP_DIR_REQUEST,
                                    op=EP_OPERATION_ADD,
                                    deadline=self.deadline)

        self.vbs.connection.send_message(mac_reports_req, MAC_REPORTS_REQ)

    def handle_response(self, meas):
        """Handle an incoming MAC_REPORTS_RESP message.
        Args:
            meas, a MAC_REPORTS_RESP message
        Returns:
            None
        """

        self.results['DL_prbs_total'] = meas.DL_prbs_total
        self.results['DL_prbs_in_use'] = meas.DL_prbs_in_use
        self.results['DL_prbs_avg'] = meas.DL_prbs_avg
        self.results['UL_prbs_total'] = meas.UL_prbs_total
        self.results['UL_prbs_in_use'] = meas.UL_prbs_in_use
        self.results['UL_prbs_avg'] = meas.UL_prbs_avg

        # call callback
        self.handle_callback(self)


class MACReportsWorker(ModuleVBSPWorker):
    """ Counter worker. """

    pass


def mac_reports(**kwargs):
    """Create a new module."""

    module = MACReportsWorker.__module__
    return RUNTIME.components[module].add_module(**kwargs)


def bound_mac_reports(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return mac_reports(**kwargs)

setattr(EmpowerApp, MACReports.MODULE_NAME, bound_mac_reports)


def launch():
    """ Initialize the module. """

    return MACReportsWorker(MACReports, EP_ACT_MAC_REPORTS, MAC_REPORTS_RESP)
