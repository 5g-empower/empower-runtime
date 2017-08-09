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

"""TXP bin counters module."""

from construct import UBInt8
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import UBInt16
from construct import UBInt32
from construct import Array

from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.module import Module
from empower.core.app import EmpowerApp
from empower.core.resourcepool import ResourceBlock
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME


PT_TXP_BIN_COUNTER_REQUEST = 0x34
PT_TXP_BIN_COUNTER_RESPONSE = 0x35

STATS = Sequence("stats", UBInt16("bytes"), UBInt32("count"))

TXP_BIN_COUNTER_REQUEST = \
    Struct("txp_bin_counter_request",
           UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           Bytes("mcast", 6),)

TXP_BIN_COUNTER_RESPONSE = \
    Struct("txp_bin_counter_response",
           UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("wtp", 6),
           UBInt16("nb_tx"),
           Array(lambda ctx: ctx.nb_tx, STATS))


class TXPBinCounter(Module):
    """ PacketsCounter object. """

    MODULE_NAME = "txp_bin_counter"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block', 'mcast']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._mcast = None
        self._bins = [8192]
        self._block = None

        # data structures
        self.tx_packets = []
        self.tx_bytes = []

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.mcast == other.mcast and \
            self.block == other.block and \
            self.bins == other.bins

    @property
    def mcast(self):
        """Return the MCAT Address."""

        return self._mcast

    @mcast.setter
    def mcast(self, value):
        """Set the mcast Address."""

        self._mcast = EtherAddress(value)

    @property
    def bins(self):
        """ Return the lvaps list """

        return self._bins

    @bins.setter
    def bins(self, bins):
        """ Set the distribution bins. Default is [ 8192 ]. """

        if len(bins) > 0:

            if [x for x in bins if isinstance(x, int)] != bins:
                raise ValueError("bins values must be integers")

            if sorted(bins) != bins:
                raise ValueError("bins must be monotonically increasing")

            if sorted(set(bins)) != sorted(bins):
                raise ValueError("bins values must not contain duplicates")

            if [x for x in bins if x > 0] != bins:
                raise ValueError("bins values must be positive")

        self._bins = bins

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

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Stats """

        out = super().to_dict()

        out['bins'] = self.bins
        out['mcast'] = self.mcast
        out['tx_bytes'] = self.tx_bytes
        out['tx_packets'] = self.tx_packets

        return out

    def run_once(self):
        """ Send out stats request. """

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

        if not wtp.connection or wtp.connection.stream.closed():
            self.log.info("WTP %s not connected", wtp.addr)
            self.unload()
            return

        stats_req = Container(version=PT_VERSION,
                              type=PT_TXP_BIN_COUNTER_REQUEST,
                              length=28,
                              seq=wtp.seq,
                              module_id=self.module_id,
                              wtp=wtp.addr.to_raw(),
                              hwaddr=self.block.hwaddr.to_raw(),
                              channel=self.block.channel,
                              band=self.block.band,
                              mcast=self.mcast.to_raw())

        self.log.info("Sending %s request to %s @ %s (id=%u)",
                      self.MODULE_NAME, self.mcast, wtp.addr,
                      self.module_id)

        msg = TXP_BIN_COUNTER_REQUEST.build(stats_req)
        wtp.connection.stream.write(msg)

    def fill_bytes_samples(self, data):
        """ Compute samples.

        Samples are in the following format (after ordering):

        [[60, 3], [66, 2], [74, 1], [98, 40], [167, 2], [209, 2], [1466, 1762]]

        Each 2-tuple has format [ size, count ] where count is the number of
        size-long (bytes, including the Ethernet 2 header) TX/RX by the LVAP.

        """

        samples = sorted(data, key=lambda entry: entry[0])
        out = [0] * len(self.bins)

        for entry in samples:
            if len(entry) == 0:
                continue
            size = entry[0]
            count = entry[1]
            for i in range(0, len(self.bins)):
                if size <= self.bins[i]:
                    out[i] = out[i] + size * count
                    break

        return out

    def fill_packets_samples(self, data):
        """ Compute samples.

        Samples are in the following format (after ordering):

        [[60, 3], [66, 2], [74, 1], [98, 40], [167, 2], [209, 2], [1466, 1762]]

        Each 2-tuple has format [ size, count ] where count is the number of
        size-long (bytes, including the Ethernet 2 header) TX/RX by the LVAP.

        """

        samples = sorted(data, key=lambda entry: entry[0])
        out = [0] * len(self.bins)

        for entry in samples:
            if len(entry) == 0:
                continue
            size = entry[0]
            count = entry[1]
            for i in range(0, len(self.bins)):
                if size <= self.bins[i]:
                    out[i] = out[i] + count
                    break

        return out

    def handle_response(self, response):
        """Handle an incoming STATS_RESPONSE message.
        Args:
            stats, a STATS_RESPONSE message
        Returns:
            None
        """

        # update this object
        self.tx_bytes = self.fill_bytes_samples(response.stats)
        self.tx_packets = self.fill_packets_samples(response.stats)

        # call callback
        self.handle_callback(self)


class TXPBinCounterWorker(ModuleLVAPPWorker):
    """Counter worker."""

    pass


def txp_bin_counter(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[TXPBinCounter.__module__]
    return worker.add_module(**kwargs)


def bound_txp_bin_counter(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return txp_bin_counter(**kwargs)


setattr(EmpowerApp, TXPBinCounter.MODULE_NAME, bound_txp_bin_counter)


def launch():
    """ Initialize the module. """

    return TXPBinCounterWorker(TXPBinCounter, PT_TXP_BIN_COUNTER_RESPONSE,
                               TXP_BIN_COUNTER_RESPONSE)
