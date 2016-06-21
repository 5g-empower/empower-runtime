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

"""Summary triggers module."""

from construct import Container
from construct import Struct
from construct import SBInt8
from construct import UBInt8
from construct import UBInt16
from construct import SBInt16
from construct import UBInt32
from construct import UBInt64
from construct import Bytes
from construct import Sequence
from construct import Array

from empower.core.resourcepool import BT_L20
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp import PT_VERSION
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.lvapp import PT_BYE
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.core.module import Module

from empower.main import RUNTIME

PT_ADD_SUMMARY = 0x22
PT_SUMMARY = 0x23
PT_DEL_SUMMARY = 0x24

ADD_SUMMARY = Struct("add_summary", UBInt8("version"),
                     UBInt8("type"),
                     UBInt16("length"),
                     UBInt32("seq"),
                     UBInt32("module_id"),
                     Bytes("addrs", 6),
                     Bytes("hwaddr", 6),
                     UBInt8("channel"),
                     UBInt8("band"),
                     SBInt16("limit"),
                     UBInt16("every"))

SUMMARY_ENTRY = Sequence("frames",
                         Bytes("addr", 6),
                         UBInt64("tsft"),
                         UBInt16("seq"),
                         SBInt8("rssi"),
                         UBInt8("rate"),
                         UBInt8("type"),
                         UBInt8("subtype"),
                         UBInt32("length"))

SUMMARY_TRIGGER = Struct("summary", UBInt8("version"),
                         UBInt8("type"),
                         UBInt16("length"),
                         UBInt32("seq"),
                         UBInt32("module_id"),
                         Bytes("wtp", 6),
                         UBInt16("nb_entries"),
                         Array(lambda ctx: ctx.nb_entries, SUMMARY_ENTRY))

DEL_SUMMARY = Struct("del_summary", UBInt8("version"),
                     UBInt8("type"),
                     UBInt16("length"),
                     UBInt32("seq"),
                     UBInt32("module_id"))


class Summary(Module):
    """ Summary object. """

    MODULE_NAME = "summary"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block', 'addrs']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._addrs = None
        self._block = None
        self._limit = -1

        # data structures
        self.frames = []

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.addrs == other.addrs and \
            self.block == other.block and \
            self.limit == other.limit

    @property
    def addrs(self):
        """ Return the address. """
        return self._addrs

    @addrs.setter
    def addrs(self, addr):
        """ Set the address. """
        self._addrs = EtherAddress(addr)

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
    def limit(self):
        """Return limit parameter."""

        return self._limit

    @limit.setter
    def limit(self, value):
        "Set limit parameter."

        if value < -1:
            raise ValueError("Invalid limit value (%u)" % value)
        self._limit = value

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Summary """

        out = super().to_dict()

        out['addrs'] = self.addrs
        out['block'] = self.block
        out['limit'] = self.limit
        out['frames'] = self.frames

        return out

    def run_once(self):
        """ Send out rate request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]
        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            self.unload()
            return

        if not wtp.connection:
            self.unload()
            return

        req = Container(version=PT_VERSION,
                        type=PT_ADD_SUMMARY,
                        length=30,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        limit=self.limit,
                        every=self.every,
                        wtp=wtp.addr.to_raw(),
                        addrs=self.addrs.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, self.block, self.module_id)

        msg = ADD_SUMMARY.build(req)
        wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming response message.
        Args:
            message, a response message
        Returns:
            None
        """

        wtp_addr = EtherAddress(response.wtp)

        if wtp_addr not in RUNTIME.wtps:
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if wtp_addr not in tenant.wtps:
            self.unload()
            return

        self.frames = []

        for recv in response.frames:

            if self.block.band == BT_L20:
                rate = float(recv[4]) / 2
            else:
                rate = int(recv[4])

            if recv[5] == 0x00:
                pt_type = "MNGT"
            elif recv[5] == 0x04:
                pt_type = "CTRL"
            elif recv[5] == 0x08:
                pt_type = "DATA"
            else:
                pt_type = "UNKN"

            if recv[6] == 0x00:
                pt_subtype = "ASSOC_REQ"
            elif recv[6] == 0x10:
                pt_subtype = "ASSOC_RESP"
            elif recv[6] == 0x20:
                pt_subtype = "AUTH_REQ"
            elif recv[6] == 0x30:
                pt_subtype = "AUTH_RESP"
            elif recv[6] == 0x80:
                pt_subtype = "BEACON"
            else:
                pt_subtype = recv[6]

            frame = {'tsft': recv[1],
                     'seq': recv[2],
                     'rssi': recv[3],
                     'rate': rate,
                     'type': pt_type,
                     'subtype': pt_subtype,
                     'length': recv[7]}

            self.frames.append(frame)

        self.handle_callback(self)


class SummaryWorker(ModuleLVAPPWorker):
    """ Summary worker. """

    def handle_bye(self, wtp):
        """Handle WTP bye message."""

        to_be_removed = []

        for module in self.modules:
            block = self.modules[module].block
            if block in wtp.supports:
                to_be_removed.append(module)

        for module in to_be_removed:
            self.remove_module(module)


def summary(**kwargs):
    """Create a new module."""

    return RUNTIME.components[SummaryWorker.__module__].add_module(**kwargs)


def bound_summary(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    kwargs['every'] = -1
    return summary(**kwargs)

setattr(EmpowerApp, Summary.MODULE_NAME, bound_summary)


def launch():
    """ Initialize the module. """

    summary_worker = SummaryWorker(Summary, PT_SUMMARY, SUMMARY_TRIGGER)
    summary_worker.pnfp_server.register_message(PT_BYE, None,
                                                summary_worker.handle_bye)
    return summary_worker
