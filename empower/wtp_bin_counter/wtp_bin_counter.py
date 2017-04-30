#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

"""WTP bin counter module."""

import time

from construct import UBInt8
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import UBInt16
from construct import UBInt32
from construct import Array

from empower.lvapp import PT_VERSION
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import LVAPPServer
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.module import Module
from empower.core.app import EmpowerApp

from empower.main import RUNTIME


PT_WTP_STATS_REQUEST = 0x41
PT_WTP_STATS_RESPONSE = 0x42

WTP_STATS = Sequence("stats",
                     Bytes("lvap", 6),
                     UBInt16("bytes"),
                     UBInt32("count"))

WTP_STATS_REQUEST = Struct("stats_request", UBInt8("version"),
                           UBInt8("type"),
                           UBInt32("length"),
                           UBInt32("seq"),
                           UBInt32("module_id"))

WTP_STATS_RESPONSE = \
    Struct("stats_response", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("wtp", 6),
           UBInt16("nb_tx"),
           UBInt16("nb_rx"),
           Array(lambda ctx: ctx.nb_tx + ctx.nb_rx, WTP_STATS))


class WTPBinCounter(Module):
    """ WTPBinCounter object.

    This primitive tracks the packets/bytes sent and received by a LVAP (which
    is the virtual AP running in the WTP). Traffic is classified in the
    specifed bins.

    For example:

        wtp_bin_counter(bins=[512, 1514, 8192],
                        wtp="11:22:33:44:55:66",
                        2000,
                        callback=counters_callback)

    This classifies the traffic TX/RX by the client lvap into the specified
    bins. Notice that with packet we mean the entire L2 PDU (Ethernet). In the
    first bin there will be all the packets whose length is smaller than or
    uqual to 512 bytes, in the second bin there will be all the packets whose
    length is smaller than or equal to 1514 bytes, in the last bin there will
    be all the packets whose length is smaller than or equal to 8192 bytes,
    """

    MODULE_NAME = "wtp_bin_counter"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'wtp']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._wtp = None
        self._bins = [8192]

        # data structures
        self.tx_packets = {}
        self.rx_packets = {}
        self.tx_bytes = {}
        self.rx_bytes = {}
        self.tx_packets_per_second = {}
        self.rx_packets_per_second = {}
        self.tx_bytes_per_second = {}
        self.rx_bytes_per_second = {}

        self.last = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.wtp == other.wtp and \
            self.bins == other.bins

    @property
    def wtp(self):
        """Return the WTP Address."""

        return self._wtp

    @wtp.setter
    def wtp(self, value):
        """Set the WTP Address."""

        self._wtp = EtherAddress(value)

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
        out['wtp'] = self.wtp
        out['tx_bytes'] = {str(k): v for k, v in self.tx_bytes.items()}
        out['rx_bytes'] = {str(k): v for k, v in self.rx_bytes.items()}
        out['tx_packets'] = {str(k): v for k, v in self.tx_packets.items()}
        out['rx_packets'] = {str(k): v for k, v in self.rx_packets.items()}
        out['tx_bytes_per_second'] = \
            {str(k): v for k, v in self.tx_bytes_per_second.items()}
        out['rx_bytes_per_second'] = \
            {str(k): v for k, v in self.rx_bytes_per_second.items()}
        out['tx_packets_per_second'] = \
            {str(k): v for k, v in self.tx_packets_per_second.items()}
        out['rx_packets_per_second'] = \
            {str(k): v for k, v in self.rx_packets_per_second.items()}

        return out

    def run_once(self):
        """ Send out stats request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.wtp not in tenant.wtps:
            self.log.info("WTP %s not found", self.wtp)
            self.unload()
            return

        wtp = tenant.wtps[self.wtp]

        if not wtp.connection or wtp.connection.stream.closed():
            self.log.info("WTP %s not connected", lvap.wtp.addr)
            self.unload()
            return

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        stats_req = Container(version=PT_VERSION,
                              type=PT_WTP_STATS_REQUEST,
                              length=14,
                              seq=wtp.seq,
                              module_id=self.module_id)

        msg = WTP_STATS_REQUEST.build(stats_req)
        wtp.connection.stream.write(msg)

    def update_stats(self, delta, last, current):
        """Update stats."""

        stats = {}

        for lvap in current.keys():

            if lvap not in last:
                continue

            stats[lvap] = []

            for i in range(0, len(last[lvap])):
                diff = current[lvap][i] - last[lvap][i]
                stats[lvap].append(diff / delta)

        return stats

    def fill_packets_sample(self, values):

        out = {}

        for value in values:
            lvap = EtherAddress(value[0])
            if lvap not in out:
                out[lvap] = []
            out[lvap].append([value[1], value[2]])

        for lvap in out.keys():

            data = out[lvap]

            samples = sorted(data, key=lambda entry: entry[0])
            new_out = [0] * len(self.bins)

            for entry in samples:
                if len(entry) == 0:
                    continue
                size = entry[0]
                count = entry[1]
                for i in range(0, len(self.bins)):
                    if size <= self.bins[i]:
                        new_out[i] = new_out[i] + count
                        break

            out[lvap] = new_out

        return out

    def fill_bytes_sample(self, values):

        out = {}

        for value in values:
            lvap = EtherAddress(value[0])
            if lvap not in out:
                out[lvap] = []
            out[lvap].append([value[1], value[2]])

        for lvap in out.keys():

            data = out[lvap]

            samples = sorted(data, key=lambda entry: entry[0])
            new_out = [0] * len(self.bins)

            for entry in samples:
                if len(entry) == 0:
                    continue
                size = entry[0]
                count = entry[1]
                for i in range(0, len(self.bins)):
                    if size <= self.bins[i]:
                        new_out[i] = new_out[i] + size * count
                        break

            out[lvap] = new_out

        return out

    def handle_response(self, response):
        """Handle an incoming STATS_RESPONSE message.
        Args:
            stats, a STATS_RESPONSE message
        Returns:
            None
        """

        tx_samples = response.stats[0:response.nb_tx]
        rx_samples = response.stats[response.nb_tx:-1]

        old_tx_bytes = self.tx_bytes
        old_rx_bytes = self.rx_bytes

        old_tx_packets = self.tx_packets
        old_rx_packets = self.rx_packets

        self.tx_bytes = self.fill_bytes_sample(tx_samples)
        self.rx_bytes = self.fill_bytes_sample(rx_samples)

        self.tx_packets = self.fill_packets_sample(tx_samples)
        self.rx_packets = self.fill_packets_sample(rx_samples)

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


class WTPBinCounterWorker(ModuleLVAPPWorker):
    """Counter worker."""

    pass


def wtp_bin_counter(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[WTPBinCounterWorker.__module__]
    return worker.add_module(**kwargs)


def bound_wtp_bin_counter(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return wtp_bin_counter(**kwargs)

setattr(EmpowerApp, WTPBinCounter.MODULE_NAME, bound_wtp_bin_counter)


def launch():
    """ Initialize the module. """

    return WTPBinCounterWorker(WTPBinCounter, PT_WTP_STATS_RESPONSE,
                               WTP_STATS_RESPONSE)
