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

from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.core.resourcepool import BT_L20
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp import PT_VERSION
from empower.core.module import Module
from empower.core.module import ModuleLVAPPWorker

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
                     UBInt16("period"))

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
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    # parametes
    _addrs = EtherAddress('FF:FF:FF:FF:FF:FF')
    _keep = 0
    _limit = -1
    _period = 2000
    _block = None

    # data structures
    frames = []

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
    def keep(self):
        """Return keep parameter."""

        return self._keep

    @keep.setter
    def keep(self, value):
        "Set keep parameter."

        if value < 0:
            raise ValueError("Invalid keep value (%u)" % value)
        self._keep = value

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

    @property
    def period(self):
        "Return period parameter."

        return self._period

    @period.setter
    def period(self, value):
        "Set period parameter."

        if value < 2000:
            raise ValueError("Invalid period value (%u)" % value)
        self._period = value

    @property
    def addrs(self):
        """ Return the address. """
        return self._addrs

    @addrs.setter
    def addrs(self, addrs):
        """ Set the address. """
        self._addrs = EtherAddress(addrs)

    def __eq__(self, other):
        return super().__eq__(other) and self.addrs == other.addrs and \
            self.limit == other.limit and self.period == other.period

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
                        type=PT_ADD_SUMMARY,
                        length=30,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        limit=self.limit,
                        period=self.period,
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
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if wtp_addr not in tenant.wtps:
            return

        if len(self.frames) > self.keep:
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

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Summary """

        out = super().to_dict()

        out['addrs'] = self.addrs
        out['keep'] = self.keep
        out['limit'] = self.limit
        out['period'] = self.period
        out['frames'] = self.frames

        return out


class SummaryWorker(ModuleLVAPPWorker):
    """ Summary worker. """

    pass


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

    return SummaryWorker(Summary, PT_SUMMARY, SUMMARY_TRIGGER)
