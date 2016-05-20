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

"""Common channel quality and conflict maps module."""

from construct import Container
from construct import Struct
from construct import Array
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import SBInt32
from construct import Sequence

from empower.datatypes.etheraddress import EtherAddress
from empower.core.resourcepool import CQM
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.core.module import Module
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME

PT_POLLER_REQ_MSG_TYPE = 0x27
PT_POLLER_RESP_MSG_TYPE = 0x28


POLLER_ENTRY_TYPE = Sequence("img_entries",
                             Bytes("addr", 6),
                             UBInt32("last_rssi_std"),
                             SBInt32("last_rssi_avg"),
                             UBInt32("last_packets"),
                             UBInt32("hist_packets"),
                             SBInt32("ewma_rssi"),
                             SBInt32("sma_rssi"))

POLLER_REQUEST = Struct("poller_request", UBInt8("version"),
                        UBInt8("type"),
                        UBInt16("length"),
                        UBInt32("seq"),
                        UBInt32("module_id"),
                        Bytes("addrs", 6),
                        Bytes("hwaddr", 6),
                        UBInt8("channel"),
                        UBInt8("band"))

POLLER_RESPONSE = Struct("poller_response", UBInt8("version"),
                         UBInt8("type"),
                         UBInt16("length"),
                         UBInt32("seq"),
                         UBInt32("module_id"),
                         Bytes("wtp", 6),
                         Bytes("hwaddr", 6),
                         UBInt8("channel"),
                         UBInt8("band"),
                         UBInt16("nb_entries"),
                         Array(lambda ctx: ctx.nb_entries, POLLER_ENTRY_TYPE))


class Maps(Module):
    """ A maps poller. """

    MODULE_NAME = None
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    _addrs = EtherAddress('FF:FF:FF:FF:FF:FF')
    _block = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.addrs == other.addrs and \
            self.block == other.block

    @property
    def addrs(self):
        return self._addrs

    @addrs.setter
    def addrs(self, value):
        self._addrs = EtherAddress(value)

    @property
    def block(self):
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
    def maps(self):
        """ Return a JSON-serializable dictionary. """

        if hasattr(self.block, self.MODULE_NAME):
            return getattr(self.block, self.MODULE_NAME)
        else:
            return {}

    def to_dict(self):
        """ Return a JSON-serializable dictionary. """

        out = super().to_dict()

        out['maps'] = {str(k): v for k, v in self.maps.items()}
        out['addrs'] = self.addrs
        out['block'] = self.block.to_dict()

        del out['block']['ucqm']
        del out['block']['ncqm']

        return out

    def run_once(self):
        """ Send out request. """

        if self.tenant_id not in RUNTIME.tenants:
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            return

        if not wtp.connection:
            return

        req = Container(version=PT_VERSION,
                        type=self.PT_REQUEST,
                        length=26,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        addrs=self.addrs.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, self.block, self.module_id)

        msg = POLLER_REQUEST.build(req)
        wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming poller response message.
        Args:
            message, a poller response message
        Returns:
            None
        """

        wtp_addr = EtherAddress(response.wtp)

        if wtp_addr not in RUNTIME.wtps:
            return

        wtp = RUNTIME.wtps[wtp_addr]

        hwaddr = EtherAddress(response.hwaddr)
        block = ResourceBlock(wtp, hwaddr, response.channel, response.band)
        incoming = ResourcePool()
        incoming.add(block)

        matching = (wtp.supports & incoming).pop()

        if not matching:
            return

        # handle the message
        setattr(self.block, self.MODULE_NAME, CQM())
        map_entry = getattr(self.block, self.MODULE_NAME)

        for entry in response.img_entries:

            addr = EtherAddress(entry[0])

            if not addr.match(self.addrs):
                continue

            value = {'addr': addr,
                     'last_rssi_std': entry[1] / 1000.0,
                     'last_rssi_avg': entry[2] / 1000.0,
                     'last_packets': entry[3],
                     'hist_packets': entry[4],
                     'ewma_rssi': entry[5] / 1000.0,
                     'sma_rssi': entry[6] / 1000.0}

            map_entry[addr] = value

        # call callback
        self.handle_callback(self)
