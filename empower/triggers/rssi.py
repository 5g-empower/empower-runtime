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
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp import PT_VERSION
from empower.core.app import EmpowerApp
from empower.triggers.trigger import Trigger
from empower.lvapp import PT_BYE

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
                          Bytes("addrs", 6),
                          Bytes("hwaddr", 6),
                          UBInt8("channel"),
                          UBInt8("band"),
                          UBInt8("relation"),
                          SBInt8("value"))

RSSI_TRIGGER = Struct("rssi_trigger", UBInt8("version"),
                      UBInt8("type"),
                      UBInt16("length"),
                      UBInt32("seq"),
                      UBInt32("module_id"),
                      Bytes("wtp", 6),
                      Bytes("addr", 6),
                      SBInt8("current"))


DEL_RSSI_TRIGGER = Struct("del_rssi_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt16("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"))


class RSSI(Trigger):
    """ RSSI trigger object. """

    MODULE_NAME = "rssi"

    def __init__(self):

        Trigger.__init__(self)

        # parameters
        self._relation = 'GT'
        self._value = -90

        # data structures
        self.events = []

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.relation == other.relation and \
            self.value == other.value

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

        out['relation'] = self.relation
        out['value'] = self.value
        out['events'] = self.events

        return out

    def run_once(self):
        """ Send out rate request. """

        if self.tenant_id not in RUNTIME.tenants:
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            return

        if not wtp.connection:
            return

        req = Container(version=PT_VERSION,
                        type=PT_ADD_RSSI,
                        length=30,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        addrs=self.addrs.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band,
                        relation=RELATIONS[self.relation],
                        value=self.value)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, self.block, self.module_id)

        msg = ADD_RSSI_TRIGGER.build(req)
        wtp.connection.stream.write(msg)

    def handle_response(self, message):
        """ Handle an incoming RSSI_TRIGGER message.
        Args:
            message, a RSSI_TRIGGER message
        Returns:
            None
        """

        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        rssi_event = {'timestamp': timestamp,
                      'addrs': self.addrs,
                      'addr': EtherAddress(message.addr),
                      'wtp': EtherAddress(message.wtp),
                      'relation': self.relation,
                      'value': self.value,
                      'current': message.current}

        self.events.append(rssi_event)
        self.handle_callback(self)


class RssiWorker(ModuleLVAPPWorker):
    """ Rssi worker. """

    def handle_bye(self, wtp):
        """Handle WTP bye message."""

        to_be_removed = []

        for module in self.modules:
            block = self.modules[module].block
            if block in wtp.supports:
                to_be_removed.append(module)

        for module in to_be_removed:
            self.remove_module(module)


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
    return rssi_worker
