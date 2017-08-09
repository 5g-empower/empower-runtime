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
from construct import BitStruct
from construct import Padding
from construct import Bit

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp import PT_VERSION
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.lvapp import PT_REGISTER
from empower.core.resourcepool import ResourceBlock
from empower.core.module import ModuleTrigger

from empower.main import RUNTIME

PT_ADD_SUMMARY = 0x22
PT_SUMMARY = 0x23
PT_DEL_SUMMARY = 0x24

ADD_SUMMARY = Struct("add_summary", UBInt8("version"),
                     UBInt8("type"),
                     UBInt32("length"),
                     UBInt32("seq"),
                     UBInt32("module_id"),
                     Bytes("addr", 6),
                     Bytes("hwaddr", 6),
                     UBInt8("channel"),
                     UBInt8("band"),
                     SBInt16("limit"),
                     UBInt16("period"))

SUMMARY_ENTRY = Sequence("frames",
                         Bytes("ra", 6),
                         Bytes("ta", 6),
                         UBInt64("tsft"),
                         BitStruct("flags",
                                   Padding(6),
                                   Bit("mcs"),
                                   Padding(9)),
                         UBInt16("seq"),
                         SBInt8("rssi"),
                         UBInt8("rate"),
                         UBInt8("type"),
                         UBInt8("subtype"),
                         UBInt32("length"))

SUMMARY_TRIGGER = Struct("summary", UBInt8("version"),
                         UBInt8("type"),
                         UBInt32("length"),
                         UBInt32("seq"),
                         UBInt32("module_id"),
                         Bytes("wtp", 6),
                         UBInt16("nb_entries"),
                         Array(lambda ctx: ctx.nb_entries, SUMMARY_ENTRY))

DEL_SUMMARY = Struct("del_summary", UBInt8("version"),
                     UBInt8("type"),
                     UBInt32("length"),
                     UBInt32("seq"),
                     UBInt32("module_id"))


class Summary(ModuleTrigger):
    """ Summary object. """

    MODULE_NAME = "summary"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    def __init__(self):

        ModuleTrigger.__init__(self)

        # parameters
        self._addr = EtherAddress("FF:FF:FF:FF:FF:FF")
        self._block = None
        self._limit = -1
        self._period = 2000

        # data structures
        self.frames = []

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.addr == other.addr and \
            self.block == other.block and \
            self.limit == other.limit

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

        out['addr'] = self.addr
        out['block'] = self.block
        out['limit'] = self.limit
        out['frames'] = self.frames

        return out

    def run_once(self):
        """ Send out rate request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found.", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]
        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            self.log.info("WTP %s not found", wtp.addr)
            self.unload()
            return

        req = Container(version=PT_VERSION,
                        type=PT_ADD_SUMMARY,
                        length=32,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        limit=self.limit,
                        period=self.period,
                        wtp=wtp.addr.to_raw(),
                        addr=self.addr.to_raw(),
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

        self.frames = []

        for recv in response.frames:

            if recv[3].mcs:
                rate = int(recv[6])
            else:
                rate = float(recv[6]) / 2

            if recv[3].mcs:
                rtype = "HT"
            else:
                rtype = "LE"

            if recv[7] == 0x00:
                pt_type = "MNGT"
            elif recv[7] == 0x04:
                pt_type = "CTRL"
            elif recv[7] == 0x08:
                pt_type = "DATA"
            else:
                pt_type = "DATA (%s)" % recv[7]

            if pt_type == "MNGT":

                if recv[8] == 0x00:
                    pt_subtype = "ASSOCREQ"
                elif recv[8] == 0x10:
                    pt_subtype = "ASSOCRESP"
                elif recv[8] == 0x20:
                    pt_subtype = "AUTHREQ"
                elif recv[8] == 0x30:
                    pt_subtype = "AUTHRESP"
                elif recv[8] == 0x40:
                    pt_subtype = "PROBEREQ"
                elif recv[8] == 0x50:
                    pt_subtype = "PROBERESP"
                elif recv[8] == 0x80:
                    pt_subtype = "BEACON"
                elif recv[8] == 0x90:
                    pt_subtype = "ATIM"
                elif recv[8] == 0xA0:
                    pt_subtype = "DISASSOC"
                elif recv[8] == 0xb0:
                    pt_subtype = "AUTH"
                elif recv[8] == 0xc0:
                    pt_subtype = "DEAUTH"
                elif recv[8] == 0xd0:
                    pt_subtype = "ACTION"
                else:
                    pt_subtype = "MNGT (%s)" % recv[8]

            elif pt_type == "CTRL":

                pt_subtype = "UNKN (%s)" % recv[8]

            elif pt_type == "DATA":

                if recv[8] == 0x00:
                    pt_subtype = "DATA"
                elif recv[8] == 0x40:
                    pt_subtype = "DATA"
                elif recv[8] == 0x80:
                    pt_subtype = "QOS"
                elif recv[8] == 0xC0:
                    pt_subtype = "QOSNULL"
                else:
                    pt_subtype = "UNKN (%s)" % recv[8]

            frame = {'ra': EtherAddress(recv[0]),
                     'ta': EtherAddress(recv[1]),
                     'tsft': recv[2],
                     'seq': recv[4],
                     'rssi': recv[5],
                     'rate': rate,
                     'rtype': rtype,
                     'type': pt_type,
                     'subtype': pt_subtype,
                     'length': recv[9]}

            self.frames.append(frame)

        self.handle_callback(self)


class SummaryWorker(ModuleLVAPPWorker):
    """ Summary worker. """

    def handle_caps(self, wtp):
        """Handle WTP CAPS message."""

        for module in self.modules:
            block = self.modules[module].block
            if block in wtp.supports:
                self.modules[module].run_once()


def summary(**kwargs):
    """Create a new module."""

    return RUNTIME.components[SummaryWorker.__module__].add_module(**kwargs)


def bound_summary(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return summary(**kwargs)

setattr(EmpowerApp, Summary.MODULE_NAME, bound_summary)


def launch():
    """ Initialize the module. """

    summary_worker = SummaryWorker(Summary, PT_SUMMARY, SUMMARY_TRIGGER)
    summary_worker.pnfp_server.register_message(PT_REGISTER, None,
                                                summary_worker.handle_caps)
    return summary_worker
