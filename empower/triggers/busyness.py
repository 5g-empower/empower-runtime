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

"""Busyness triggers module."""

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

PT_ADD_BUSYNESS = 0x38
PT_BUSYNESS = 0x39
PT_DEL_BUSYNESS = 0x40

ADD_BUSYNESS_TRIGGER = Struct("add_busyness_trigger", UBInt8("version"),
                              UBInt8("type"),
                              UBInt32("length"),
                              UBInt32("seq"),
                              UBInt32("module_id"),
                              Bytes("hwaddr", 6),
                              UBInt8("channel"),
                              UBInt8("band"),
                              UBInt8("relation"),
                              UBInt32("value"),
                              UBInt16("period"))

BUSYNESS_TRIGGER = Struct("busyness_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt32("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"),
                          Bytes("wtp", 6),
                          Bytes("hwaddr", 6),
                          UBInt8("channel"),
                          UBInt8("band"),
                          UBInt32("current"))

DEL_BUSYNESS_TRIGGER = Struct("del_busyness_trigger", UBInt8("version"),
                              UBInt8("type"),
                              UBInt32("length"),
                              UBInt32("seq"),
                              UBInt32("module_id"))


class BusynessTrigger(ModuleTrigger):
    """ Busyness trigger object. """

    MODULE_NAME = "busyness_trigger"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    def __init__(self):

        ModuleTrigger.__init__(self)

        # parameters
        self._block = None
        self._relation = 'GT'
        self._value = 0.0
        self._period = 2000

        # data structures
        # list of wtps address to which the add busyness message has been sent
        self.wtps = []
        self.event = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.block == other.block and \
            self.relation == other.relation and \
            self.value == other.value and \
            self.period == other.period

    @property
    def block(self):
        """Return block."""

        return self._block

    @block.setter
    def block(self, value):

        if isinstance(value, ResourceBlock):

            self._block = value

        elif isinstance(value, dict):

            wtp = RUNTIME.wtps[EtherAddress(value['wtp'])]

            if 'hwaddr' not in value:
                raise ValueError("Missing field: hwaddr")

            if 'channel' not in value:
                raise ValueError("Missing field: channel")

            if 'band' not in value:
                raise ValueError("Missing field: band")

            if 'wtp' not in value:
                raise ValueError("Missing field: wtp")

            # Check if block is valid
            incoming = ResourceBlock(wtp, EtherAddress(value['hwaddr']),
                                     int(value['channel']),
                                     int(value['band']))

            match = [block for block in wtp.supports if block == incoming]

            if not match:
                raise ValueError("No block specified")

            if len(match) > 1:
                raise ValueError("More than one block specified")

            self._block = match[0]

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

        if value < 0 or value > 100:
            raise ValueError("busyness requires 0 <= value <= 100")

        self._value = int(value)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Trigger """

        out = super().to_dict()

        out['block'] = self.block
        out['relation'] = self.relation
        out['value'] = self.value
        out['period'] = self.period
        out['event'] = self.event
        out['wtps'] = self.wtps

        return out

    def run_once(self):
        """ Send out rate request. """

        for wtp in RUNTIME.tenants[self.tenant_id].wtps.values():
            self.add_busyness_to_wtp(wtp)

    def add_busyness_to_wtp(self, wtp):
        """Add Busyness to WTP."""

        if not wtp.connection or wtp.connection.stream.closed():
            return

        if wtp in self.wtps:
            return

        req = Container(version=PT_VERSION,
                        type=PT_ADD_BUSYNESS,
                        length=29,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band,
                        relation=RELATIONS[self.relation],
                        value=int(self.value * 180),
                        period=self.period)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        self.wtps.append(wtp)

        msg = ADD_BUSYNESS_TRIGGER.build(req)
        wtp.connection.stream.write(msg)

    def remove_busyness_from_wtp(self, wtp):
        """Remove Busyness to WTP."""

        if not wtp.connection or wtp.connection.stream.closed():
            return

        if wtp not in self.wtps:
            return

        req = Container(version=PT_VERSION,
                        type=PT_DEL_BUSYNESS,
                        length=14,
                        seq=wtp.seq,
                        module_id=self.module_id)

        self.log.info("Sending remove %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        self.wtps.remove(wtp)

        msg = DEL_BUSYNESS_TRIGGER.build(req)
        wtp.connection.stream.write(msg)

    def handle_response(self, message):
        """ Handle an incoming BUSYNESS_TRIGGER message.
        Args:
            message, a BUSYNESS_TRIGGER message
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
             'current': message.current / 180.0}

        self.handle_callback(self)


class BusynessTriggerWorker(ModuleLVAPPWorker):
    """ Busyness worker. """

    def handle_caps(self, _):
        """Handle WTP CAPS message."""

        for module in self.modules.values():
            module.run_once()

    def handle_bye(self, wtp):
        """Handle WTP BYE message."""

        for module in self.modules.values():
            module.wtps.remove(wtp)


def busyness_trigger(**kwargs):
    """Create a new module."""

    module = RUNTIME.components[BusynessTriggerWorker.__module__]
    return module.add_module(**kwargs)


def bound_busyness_trigger(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return busyness_trigger(**kwargs)

setattr(EmpowerApp, BusynessTrigger.MODULE_NAME, bound_busyness_trigger)


def launch():
    """ Initialize the module. """

    busyness_worker = BusynessTriggerWorker(BusynessTrigger, PT_BUSYNESS,
                                            BUSYNESS_TRIGGER)
    busyness_worker.pnfp_server.register_message(PT_REGISTER, None,
                                                 busyness_worker.handle_caps)
    busyness_worker.pnfp_server.register_message(PT_BYE, None,
                                                 busyness_worker.handle_bye)

    return busyness_worker
