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

from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.lvapp import PT_VERSION
from empower.core.app import EmpowerApp
from empower.lvapp import PT_BYE
from empower.lvapp import PT_LVAP_LEAVE
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import Module

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
                          UBInt16("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"),
                          Bytes("sta", 6),
                          Bytes("hwaddr", 6),
                          UBInt8("channel"),
                          UBInt8("band"),
                          UBInt8("relation"),
                          SBInt8("value"),
                          UBInt16("period"))

RSSI_TRIGGER = Struct("rssi_trigger", UBInt8("version"),
                      UBInt8("type"),
                      UBInt16("length"),
                      UBInt32("seq"),
                      UBInt32("module_id"),
                      Bytes("wtp", 6),
                      SBInt8("current"))


DEL_RSSI_TRIGGER = Struct("del_rssi_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt16("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"))


class RSSI(Module):
    """ RSSI trigger object. """

    MODULE_NAME = "rssi"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block', 'lvap']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._lvap = None
        self._block = None
        self._relation = 'GT'
        self._value = -90
        self._period = 2000

        # data structures
        self.current = None
        self.timestamp = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.lvap == other.lvap and \
            self.block == other.block and \
            self.relation == other.relation and \
            self.value == other.value

    @property
    def lvap(self):
        """ Return the address. """

        return self._lvap

    @lvap.setter
    def lvap(self, lvap):
        """ Set the address. """
        self._lvap = EtherAddress(lvap)

    @property
    def block(self):
        """Return block."""

        return self._block

    @block.setter
    def block(self, value):
        """Set block."""

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

            incoming = ResourcePool()
            block = ResourceBlock(wtp, EtherAddress(value['hwaddr']),
                                  int(value['channel']), int(value['band']))
            incoming.add(block)

            match = wtp.supports & incoming

            if not match:
                raise ValueError("No block specified")

            if len(match) > 1:
                raise ValueError("More than one block specified")

            self._block = match.pop()

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
        out['block'] = self.block
        out['relation'] = self.relation
        out['value'] = self.value
        out['current'] = self.current
        out['timestamp'] = self.timestamp

        return out

    def run_once(self):
        """ Send out rate request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]
        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            self.log.info("WTP %s not found", wtp.addr)
            self.unload()
            return

        if self.lvap not in tenant.lvaps:
            self.log.info("LVAP %s not found", self.lvap)
            self.unload()
            return

        req = Container(version=PT_VERSION,
                        type=PT_ADD_RSSI,
                        length=30,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        sta=self.lvap.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band,
                        relation=RELATIONS[self.relation],
                        value=self.value,
                        period=self.period)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, self.block, self.module_id)

        msg = ADD_RSSI_TRIGGER.build(req)
        wtp.connection.stream.write(msg)

    def unload(self):
        """Remove this module."""

        self.log.info("Removing %s (id=%u)", self.module_type, self.module_id)
        self.worker.remove_module(self.module_id)

        wtp = self.block.radio

        if not wtp.connection or wtp.connection.stream.closed():
            return

        del_rssi = Container(version=PT_VERSION,
                             type=PT_DEL_RSSI,
                             length=12,
                             seq=wtp.seq,
                             module_id=self.module_id)

        msg = DEL_RSSI_TRIGGER.build(del_rssi)
        wtp.connection.stream.write(msg)

    def handle_response(self, message):
        """ Handle an incoming RSSI_TRIGGER message.
        Args:
            message, a RSSI_TRIGGER message
        Returns:
            None
        """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]
        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            self.log.info("WTP %s not found", wtp.addr)
            self.unload()
            return

        if self.lvap not in tenant.lvaps:
            self.log.info("LVAP %s not found", self.lvap)
            self.unload()
            return

        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.current = message.current

        self.handle_callback(self)


class RssiWorker(ModuleLVAPPWorker):
    """ Rssi worker. """

    def handle_bye(self, wtp):
        """Handle WTP bye message."""

        to_be_removed = []

        for module in self.modules.values():
            if module.block in wtp.supports:
                to_be_removed.append(module)

        for module in to_be_removed:
            module.unload()

    def handle_lvap_leave(self, lvap):
        """Handle WTP bye message."""

        to_be_removed = []

        for module in self.modules.values():
            if module.lvap == lvap.addr:
                to_be_removed.append(module)

        for module in to_be_removed:
            module.unload()


def rssi(**kwargs):
    """Create a new module."""

    return RUNTIME.components[RssiWorker.__module__].add_module(**kwargs)


def bound_rssi(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    kwargs['every'] = -1
    return rssi(**kwargs)

setattr(EmpowerApp, RSSI.MODULE_NAME, bound_rssi)


def launch():
    """ Initialize the module. """

    rssi_worker = RssiWorker(RSSI, PT_RSSI, RSSI_TRIGGER)
    rssi_worker.pnfp_server.register_message(PT_BYE, None,
                                             rssi_worker.handle_bye)
    rssi_worker.pnfp_server.register_message(PT_LVAP_LEAVE, None,
                                             rssi_worker.handle_lvap_leave)
    return rssi_worker
