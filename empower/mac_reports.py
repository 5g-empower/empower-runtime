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

"""PRB utilization module."""

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
from empower.core.module import ModuleScheduled
from empower.vbsp import PT_VERSION
from empower.vbsp import E_TYPE_SCHED
from empower.vbsp import EP_DIR_REQUEST
from empower.vbsp import EP_OPERATION_ADD

from empower.main import RUNTIME


EP_ACT_PRB_UTIL = 0x06

PRB_UTIL_REQ = Struct("prb_util_req",
                      UBInt32("length"),
                      UBInt8("type"),
                      UBInt8("version"),
                      UBInt32("enbid"),
                      UBInt16("cellid"),
                      UBInt32("modid"),
                      UBInt32("seq"),
                      UBInt8("action"),
                      UBInt8("dir"),
                      UBInt8("op"),
                      UBInt16("interval"))

PRB_UTIL_RESP = Struct("prb_util_resp",
                       UBInt8("DL_prbs_total"),
                       UBInt8("DL_prbs_in_use"),
                       UBInt16("DL_prbs_avg"),
                       UBInt8("UL_prbs_total"),
                       UBInt8("UL_prbs_in_use"),
                       UBInt16("UL_prbs_avg"))


class PRBUtilization(ModuleScheduled):
    """ LVAPStats object. """

    MODULE_NAME = "prb_utilization"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'cell', 'interval']

    def __init__(self):

        super().__init__()

        # parameters
        self._cell = None
        self._interval = None

        # stats
        self.results = []

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

            self._cell = None

            for cell in vbs.cells:
                if cell.pci == pci:
                    self._cell = cell

            if not self._cell:
                raise ValueError("Invalid pci %u", pci)

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

        prb_util_req = Container(length=25,
                                 type=E_TYPE_SCHED,
                                 version=PT_VERSION,
                                 enbid=self.vbs.enb_id,
                                 cellid=self.cell.pci,
                                 modid=self.module_id,
                                 seq=self.vbs.seq,
                                 action=EP_ACT_PRB_UTIL,
                                 dir=EP_DIR_REQUEST,
                                 op=EP_OPERATION_ADD,
                                 interval=self.interval)

        self.log.info("Sending prb util request for %s @ %s (id=%u)",
                      self.cell.pci, self.vbs.addr, self.module_id)

        msg = PRB_UTIL_REQ.build(prb_util_req)
        self.vbs.connection.stream.write(msg)

    def handle_response(self, meas):
        """Handle an incoming PRB_UTILIZATION message.
        Args:
            meas, a PRB_UTILIZATION message
        Returns:
            None
        """

        print(meas)

        # call callback
        self.handle_callback(self)


class PRBUtilizationWorker(ModuleVBSPWorker):
    """ Counter worker. """

    pass


def prb_utilization(**kwargs):
    """Create a new module."""

    module = PRBUtilizationWorker.__module__
    return RUNTIME.components[module].add_module(**kwargs)


def bound_prb_utilization(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return prb_utilization(**kwargs)

setattr(EmpowerApp, PRBUtilization.MODULE_NAME, bound_prb_utilization)


def launch():
    """ Initialize the module. """

    return PRBUtilizationWorker(PRBUtilization,
                                EP_ACT_PRB_UTIL,
                                PRB_UTIL_RESP)
