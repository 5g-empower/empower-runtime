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

"""RSSI triggers module."""

from datetime import datetime

from construct import Container
from construct import Struct
from construct import SBInt8
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes

from empower.core.resourcepool import ResourceBlock
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.lvapp import PT_VERSION
from empower.core.app import EmpowerApp
from empower.lvapp import PT_REGISTER
from empower.lvapp import PT_BYE
from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import ModuleTrigger

from empower.main import RUNTIME

R_GT = 'GT'
R_LT = 'LT'
R_EQ = 'EQ'
R_GE = 'GE'
R_LE = 'LE'

RELATIONS = {R_EQ: 0, R_GT: 1, R_LT: 2, R_GE: 3, R_LE: 4}

PT_ADD_RSSI = 0x19
PT_RSSI = 0x20
PT_DEL_RSSI = 0x21

ADD_RSSI_TRIGGER = Struct("add_rssi_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt32("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"),
                          Bytes("sta", 6),
                          UBInt8("relation"),
                          SBInt8("value"),
                          UBInt16("period"))

RSSI_TRIGGER = Struct("rssi_trigger", UBInt8("version"),
                      UBInt8("type"),
                      UBInt32("length"),
                      UBInt32("seq"),
                      UBInt32("module_id"),
                      Bytes("wtp", 6),
                      Bytes("hwaddr", 6),
                      UBInt8("channel"),
                      UBInt8("band"),
                      SBInt8("current"))

DEL_RSSI_TRIGGER = Struct("del_rssi_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt32("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"))


class RSSI(ModuleTrigger):
    """ RSSI trigger object. """

    MODULE_NAME = "rssi"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvap']

    def __init__(self):

        ModuleTrigger.__init__(self)

        # parameters
        self._lvap = None
        self._relation = 'GT'
        self._value = -90
        self._period = 2000

        # data structures
        # list of wtps address to which the add rssi message has been sent
        self.wtps = []
        self.event = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.lvap == other.lvap and \
            self.relation == other.relation and \
            self.value == other.value and \
            self.period == other.period

    @property
    def lvap(self):
        """ Return the LVAP address. """

        return self._lvap

    @lvap.setter
    def lvap(self, lvap):
        """ Set the LVAP address. """

        self._lvap = EtherAddress(lvap)

    @property
    def period(self):
        """Return period parameter."""

        return self._period

    @period.setter
    def period(self, value):
        "Set period parameter."

        if value < 1000:
            raise ValueError("Invalid limit value (%u)" % value)

        self._period = value

    @property
    def relation(self):
        """ Return the relation. """

        return self._relation

    @relation.setter
    def relation(self, relation):
        """ Set the relation. """

        if relation not in RELATIONS:
            raise ValueError("Valid relations are: %s" %
                             ','.join(RELATIONS.keys()))

        self._relation = relation

    @property
    def value(self):
        """ Return the value. """

        return self._value

    @value.setter
    def value(self, value):
        """ Set the value. """

        if value < -128 or value > 127:
            raise ValueError("rssi requires -128 <= value <= 127")

        self._value = int(value)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Trigger """

        out = super().to_dict()

        out['lvap'] = self.lvap
        out['relation'] = self.relation
        out['value'] = self.value
        out['period'] = self.period
        out['event'] = self.event
        out['wtps'] = self.wtps

        return out

    def run_once(self):
        """ Send out rate request. """

        for wtp in RUNTIME.tenants[self.tenant_id].wtps.values():
            self.add_rssi_to_wtp(wtp)

    def add_rssi_to_wtp(self, wtp):
        """Add RSSI to WTP."""

        if not wtp.connection or wtp.connection.stream.closed():
            return

        if wtp in self.wtps:
            return

        req = Container(version=PT_VERSION,
                        type=PT_ADD_RSSI,
                        length=32,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        sta=self.lvap.to_raw(),
                        relation=RELATIONS[self.relation],
                        value=self.value,
                        period=self.period)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        self.wtps.append(wtp)

        msg = ADD_RSSI_TRIGGER.build(req)
        wtp.connection.stream.write(msg)

    def remove_rssi_from_wtp(self, wtp):
        """Remove RSSI to WTP."""

        if not wtp.connection or wtp.connection.stream.closed():
            return

        if wtp not in self.wtps:
            return

        req = Container(version=PT_VERSION,
                        type=PT_DEL_RSSI,
                        length=14,
                        seq=wtp.seq,
                        module_id=self.module_id)

        self.log.info("Sending remove %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        self.wtps.remove(wtp)

        msg = DEL_RSSI_TRIGGER.build(req)
        wtp.connection.stream.write(msg)

    def handle_response(self, message):
        """ Handle an incoming RSSI_TRIGGER message.
        Args:
            message, a RSSI_TRIGGER message
        Returns:
            None
        """

        wtp_addr = EtherAddress(message.wtp)

        if wtp_addr not in RUNTIME.wtps:
            return

        wtp = RUNTIME.wtps[wtp_addr]

        if wtp_addr not in RUNTIME.tenants[self.tenant_id].wtps:
            return

        hwaddr = EtherAddress(message.hwaddr)
        channel = message.channel
        band = message.band
        incoming = ResourceBlock(wtp, hwaddr, channel, band)

        match = [block for block in wtp.supports if block == incoming]

        self.event = \
            {'block': matches[0],
             'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
             'current': message.current}

        self.handle_callback(self)


class RssiWorker(ModuleLVAPPWorker):
    """ Rssi worker. """

    def handle_caps(self, _):
        """Handle WTP CAPS message."""

        for module in self.modules.values():
            module.run_once()

    def handle_bye(self, wtp):
        """Handle WTP BYE message."""

        for module in self.modules.values():
            module.wtps.remove(wtp)


def rssi(**kwargs):
    """Create a new module."""

    return RUNTIME.components[RssiWorker.__module__].add_module(**kwargs)


def bound_rssi(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return rssi(**kwargs)

setattr(EmpowerApp, RSSI.MODULE_NAME, bound_rssi)


def launch():
    """ Initialize the module. """

    rssi_worker = RssiWorker(RSSI, PT_RSSI, RSSI_TRIGGER)
    rssi_worker.pnfp_server.register_message(PT_REGISTER, None,
                                             rssi_worker.handle_caps)
    rssi_worker.pnfp_server.register_message(PT_BYE, None,
                                             rssi_worker.handle_bye)

    return rssi_worker
