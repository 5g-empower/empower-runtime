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

"""LVAP statistics module."""

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

from empower.core.resourcepool import BT_L20
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.module import Module
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME


PT_RATES_REQUEST = 0x29
PT_RATES_RESPONSE = 0x30

RATES_ENTRY = Sequence("rates",
                       UBInt8("rate"),
                       BitStruct("flags",
                                 Padding(6),
                                 Bit("mcs"),
                                 Padding(9)),
                       UBInt32("prob"),
                       UBInt32("cur_prob"))

RATES_REQUEST = Struct("rates_request", UBInt8("version"),
                       UBInt8("type"),
                       UBInt32("length"),
                       UBInt32("seq"),
                       UBInt32("module_id"),
                       Bytes("sta", 6))

RATES_RESPONSE = Struct("rates_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt32("length"),
                        UBInt32("seq"),
                        UBInt32("module_id"),
                        Bytes("wtp", 6),
                        UBInt16("nb_entries"),
                        Array(lambda ctx: ctx.nb_entries, RATES_ENTRY))


class LVAPStats(Module):
    """ LVAPStats object. """

    MODULE_NAME = "lvap_stats"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvap']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._lvap = None

        # data structures
        self.rates = {}

    def __eq__(self, other):

        return super().__eq__(other) and self.lvap == other.lvap

    @property
    def lvap(self):
        """Return LVAP Address."""

        return self._lvap

    @lvap.setter
    def lvap(self, value):
        """Set LVAP Address."""

        self._lvap = EtherAddress(value)

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['lvap'] = self.lvap
        out['rates'] = {str(k): v for k, v in self.rates.items()}

        return out

    def run_once(self):
        """Send out rate request."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.lvap not in tenant.lvaps:
            self.log.info("LVNF %s not found", self.lvap)
            self.unload()
            return

        lvap = tenant.lvaps[self.lvap]

        if not lvap.wtp.connection or lvap.wtp.connection.stream.closed():
            self.log.info("WTP %s not connected", lvap.wtp.addr)
            self.unload()
            return

        rates_req = Container(version=PT_VERSION,
                              type=PT_RATES_REQUEST,
                              length=20,
                              seq=lvap.wtp.seq,
                              module_id=self.module_id,
                              sta=lvap.addr.to_raw())

        self.log.info("Sending rates request to %s @ %s (id=%u)",
                      lvap.addr, lvap.wtp.addr, self.module_id)

        msg = RATES_REQUEST.build(rates_req)
        lvap.wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming RATES_RESPONSE message.
        Args:
            rates, a RATES_RESPONSE message
        Returns:
            None
        """

        tenant = RUNTIME.tenants[self.tenant_id]
        lvap = tenant.lvaps[self.lvap]

        # update this object
        self.rates = {}
        for entry in response.rates:
            if lvap.supported_band == BT_L20:
                rate = entry[0] / 2.0
            else:
                rate = entry[0]
            value = {'prob': entry[2] / 180.0,
                     'cur_prob': entry[3] / 180.0, }
            self.rates[rate] = value

        # call callback
        self.handle_callback(self)


class LVAPStatsWorker(ModuleLVAPPWorker):
    """ Counter worker. """

    pass


def lvap_stats(**kwargs):
    """Create a new module."""

    return RUNTIME.components[LVAPStatsWorker.__module__].add_module(**kwargs)


def bound_lvap_stats(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return lvap_stats(**kwargs)

setattr(EmpowerApp, LVAPStats.MODULE_NAME, bound_lvap_stats)


def launch():
    """ Initialize the module. """

    return LVAPStatsWorker(LVAPStats, PT_RATES_RESPONSE, RATES_RESPONSE)
