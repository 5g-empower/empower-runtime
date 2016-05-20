#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""RSSI triggers module."""

from datetime import datetime

from construct import Container
from construct import Struct
from construct import SBInt8
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes

from empower.core.module import ModuleLVAPPWorker
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.core.module import Module
from empower.core.lvap import LVAP
from empower.datatypes.etheraddress import EtherAddress
from empower.core.app import EmpowerApp
from empower.lvapp import PT_VERSION

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
                          Bytes("addr", 6),
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
                      UBInt8("relation"),
                      SBInt8("value"),
                      SBInt8("current"))


DEL_RSSI_TRIGGER = Struct("del_rssi_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt16("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"))


class RSSI(Module):
    """ RSSI trigger object. """

    MODULE_NAME = "rssi"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'addr', 'block']

    # parameters
    _addr = None
    _relation = 'GT'
    _value = -90
    _block = None

    # data strctures
    events = []

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
                        addr=self.addr.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band,
                        relation=RELATIONS[self.relation],
                        value=self.value)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, self.block, self.module_id)

        msg = ADD_RSSI_TRIGGER.build(req)
        wtp.connection.stream.write(msg)

    @property
    def addr(self):
        """ Return the address. """
        return self._addr

    @addr.setter
    def addr(self, addr):
        """ Set the address. """
        self._addr = EtherAddress(addr)

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

    def handle_response(self, message):
        """ Handle an incoming RSSI_TRIGGER message.
        Args:
            message, a RSSI_TRIGGER message
        Returns:
            None
        """

        if message.relation == RELATIONS['EQ']:
            relation = 'EQ'
        elif message.relation == RELATIONS['GT']:
            relation = 'GT'
        elif message.relation == RELATIONS['LT']:
            relation = 'LT'
        elif message.relation == RELATIONS['GE']:
            relation = 'GE'
        elif message.relation == RELATIONS['LE']:
            relation = 'LE'

        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        rssi_event = {'timestamp': timestamp,
                      'addr': EtherAddress(message.addr),
                      'wtp': EtherAddress(message.wtp),
                      'relation': relation,
                      'value': message.value,
                      'current': message.current}

        self.events.append(rssi_event)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Trigger """

        out = super().to_dict()

        out['relation'] = self.relation
        out['addr'] = self.addr
        out['value'] = self.value
        out['events'] = self.events

        return out

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

    def __eq__(self, other):
        return self.addr == other.addr and self.relation == other.relation \
            and self.value == other.value


class RssiWorker(ModuleLVAPPWorker):
    """ Rssi worker. """

    pass


def rssi(**kwargs):
    """Create a new module."""

    return RUNTIME.components[RssiWorker.__module__].add_module(**kwargs)


def bound_rssi(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    kwargs['addr'] = self.addr
    kwargs['block'] = next(iter(self.downlink.keys()))
    kwargs['every'] = -1
    return rssi(**kwargs)

setattr(LVAP, RSSI.MODULE_NAME, bound_rssi)


def launch():
    """ Initialize the module. """

    return RssiWorker(RSSI, PT_RSSI, RSSI_TRIGGER)
