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

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.core.cellpool import Cell
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import ModuleTrigger
from empower.vbsp import E_TYPE_TRIG
from empower.vbsp import EP_OPERATION_ADD

from empower.main import RUNTIME


EP_ACT_MAC_REPORTS = 0x06

MAC_REPORTS_REQ = Struct("rrc_request",
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
                         UBInt16("deadline"))

MAC_REPORTS_RESP = Struct("mac_reports_resp",
                          UBInt8("dl_prbs_total"),
                          UBInt32("dl_prbs_used"),
                          UBInt8("ul_prbs_total"),
                          UBInt32("ul_prbs_used"))


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
        self.dl_prbs_last = 0
        self.ul_prbs_last = 0
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

            self._cell = vbs.get_cell(pci)

            if not self._cell:
                raise ValueError("Invalid pci %u" % pci)

        else:

            raise Exception("Invalid cell value %s" % value)

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

        msg = Container(deadline=self.deadline)

        self.vbs.connection.send_message(msg,
                                         E_TYPE_TRIG,
                                         EP_ACT_MAC_REPORTS,
                                         MAC_REPORTS_REQ,
                                         cellid=self.cell.pci,
                                         xid=self.module_id,
                                         opcode=EP_OPERATION_ADD)

    def handle_response(self, response):
        """Handle an incoming MAC_REPORTS_RESP message.
        Args:
            meas, a MAC_REPORTS_RESP message
        Returns:
            None
        """

        self.results['dl_prbs_total'] = response.dl_prbs_total
        self.results['dl_prbs_used'] = response.dl_prbs_used
        self.results['dl_prbs_last'] = response.dl_prbs_used - \
            self.dl_prbs_last
        self.dl_prbs_last = response.dl_prbs_used
        self.results['dl_util_last'] = float(self.results['dl_prbs_last']) / \
            (response.dl_prbs_total * self.deadline)

        self.results['ul_prbs_total'] = response.ul_prbs_total
        self.results['ul_prbs_used'] = response.ul_prbs_used
        self.results['ul_prbs_last'] = response.ul_prbs_used - \
            self.ul_prbs_last
        self.ul_prbs_last = response.ul_prbs_used
        self.results['ul_util_last'] = float(self.results['ul_prbs_last']) / \
            (response.ul_prbs_total * self.deadline)

        self.cell.mac_reports = self.results

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
