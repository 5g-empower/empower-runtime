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

"""Common bin_counter module."""

import time

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
from empower.core.lvap import LVAP
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME


PT_STATS_REQUEST = 0x17
PT_STATS_RESPONSE = 0x18

STATS = Sequence("stats", UBInt16("bytes"), UBInt32("count"))

STATS_REQUEST = Struct("stats_request", UBInt8("version"),
                       UBInt8("type"),
                       UBInt32("length"),
                       UBInt32("seq"),
                       UBInt32("module_id"),
                       Bytes("sta", 6))

STATS_RESPONSE = \
    Struct("stats_response", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("wtp", 6),
           Bytes("sta", 6),
           UBInt16("nb_tx"),
           UBInt16("nb_rx"),
           Array(lambda ctx: ctx.nb_tx + ctx.nb_rx, STATS))


class BinCounter(Module):
    """ PacketsCounter object.

    This primitive tracks the packets/bytes sent and received by a LVAP (which
    is the virtual AP running in the WTP). Traffic is classified in the
    specifed bins.

    For example:

        lvap.bin_counter(bins=[512, 1514, 8192],
                         2000,
                         callback=self.counters_callback)

    This classifies the traffic TX/RX by the client lvap into the specified
    bins. Notice that with packet we mean the entire L2 PDU (Ethernet). In the
    first bin there will be all the packets whose length is smaller than or
    uqual to 512 bytes, in the second bin there will be all the packets whose
    length is smaller than or equal to 1514 bytes, in the last bin there will
    be all the packets whose length is smaller than or equal to 8192 bytes,
    """

    MODULE_NAME = "bin_counter"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvap']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._lvap = None
        self._bins = [8192]

        # data structures
        self.tx_packets = []
        self.rx_packets = []
        self.tx_bytes = []
        self.rx_bytes = []
        self.tx_packets_per_second = []
        self.rx_packets_per_second = []
        self.tx_bytes_per_second = []
        self.rx_bytes_per_second = []

        self.last = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.lvap == other.lvap and \
            self.bins == other.bins

    @property
    def lvap(self):
        """Return the LVAP Address."""

        return self._lvap

    @lvap.setter
    def lvap(self, value):
        """Set the LVAP Address."""

        self._lvap = EtherAddress(value)

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

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Stats """

        out = super().to_dict()

        out['bins'] = self.bins
        out['lvap'] = self.lvap
        out['tx_bytes'] = self.tx_bytes
        out['rx_bytes'] = self.rx_bytes
        out['tx_packets'] = self.tx_packets
        out['rx_packets'] = self.rx_packets
        out['tx_bytes_per_second'] = self.tx_bytes_per_second
        out['rx_bytes_per_second'] = self.rx_bytes_per_second
        out['tx_packets_per_second'] = self.tx_packets_per_second
        out['rx_packets_per_second'] = self.rx_packets_per_second

        return out

    def run_once(self):
        """ Send out stats request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.lvap not in tenant.lvaps:
            self.log.info("LVAP %s not found", self.lvap)
            return

        lvap = tenant.lvaps[self.lvap]

        if not lvap.wtp.connection or lvap.wtp.connection.stream.closed():
            self.log.info("WTP %s not connected", lvap.wtp.addr)
            return

        stats_req = Container(version=PT_VERSION,
                              type=PT_STATS_REQUEST,
                              length=20,
                              seq=lvap.wtp.seq,
                              module_id=self.module_id,
                              sta=lvap.addr.to_raw())

        self.log.info("Sending %s request to %s @ %s (id=%u)",
                      self.MODULE_NAME, lvap.addr, lvap.wtp.addr,
                      self.module_id)

        msg = STATS_REQUEST.build(stats_req)
        lvap.wtp.connection.stream.write(msg)

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

    def update_stats(self, delta, last, current):
        """Update stats."""

        stats = []

        for i in range(0, len(last)):
            diff = current[i] - last[i]
            stats.append(diff / delta)

        return stats

    def handle_response(self, response):
        """Handle an incoming STATS_RESPONSE message.
        Args:
            stats, a STATS_RESPONSE message
        Returns:
            None
        """

        # update this object
        tx_samples = response.stats[0:response.nb_tx]
        rx_samples = response.stats[response.nb_tx:-1]

        old_tx_bytes = self.tx_bytes
        old_rx_bytes = self.rx_bytes

        old_tx_packets = self.tx_packets
        old_rx_packets = self.rx_packets

        self.tx_bytes = self.fill_bytes_samples(tx_samples)
        self.rx_bytes = self.fill_bytes_samples(rx_samples)

        self.tx_packets = self.fill_packets_samples(tx_samples)
        self.rx_packets = self.fill_packets_samples(rx_samples)

        if self.last:
            delta = time.time() - self.last
            self.tx_bytes_per_second = \
                self.update_stats(delta, old_tx_bytes, self.tx_bytes)
            self.rx_bytes_per_second = \
                self.update_stats(delta, old_rx_bytes, self.rx_bytes)
            self.tx_packets_per_second = \
                self.update_stats(delta, old_tx_packets, self.tx_packets)
            self.rx_packets_per_second = \
                self.update_stats(delta, old_rx_packets, self.rx_packets)

        self.last = time.time()

        # call callback
        self.handle_callback(self)


class BinCounterWorker(ModuleLVAPPWorker):
    """Counter worker."""

    pass


def bin_counter(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[BinCounterWorker.__module__]
    return worker.add_module(**kwargs)


def bound_bin_counter(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    kwargs['lvap'] = self.addr
    return bin_counter(**kwargs)

setattr(LVAP, BinCounter.MODULE_NAME, bound_bin_counter)


def launch():
    """ Initialize the module. """

    return BinCounterWorker(BinCounter, PT_STATS_RESPONSE, STATS_RESPONSE)
