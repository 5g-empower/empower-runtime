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

"""Traffic rules statistics module."""

from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import Array

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.dscp import DSCP
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.module import ModulePeriodic
from empower.core.resourcepool import ResourceBlock
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME


PT_TRQ_BIN_COUNTER_REQUEST = 0x59
PT_TRQ_BIN_COUNTER_RESPONSE = 0x60

STATS = Sequence("stats", UBInt16("bytes"), UBInt32("count"))

TRQ_BIN_COUNTER_REQUEST = \
    Struct("trq_bin_counter_request", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           UBInt8("dscp"),
           Bytes("ssid", lambda ctx: ctx.length - 23))

TRQ_BIN_COUNTER_RESPONSE = \
    Struct("trq_bin_counter_response", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("wtp", 6),
           UBInt32("deficit_used"),
           UBInt32("max_queue_length"),
           UBInt16("nb_tx"),
           Array(lambda ctx: ctx.nb_tx, STATS))


class TRQBinCounter(ModulePeriodic):
    """ TRQBinCounter object. """

    MODULE_NAME = "trq_bin_counter"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    def __init__(self):

        super().__init__()

        # parameters
        self._block = None
        self._bins = [8192]
        self._dscp = DSCP()

        # data structures
        self.tx_packets = []
        self.tx_bytes = []
        self.deficit_used = 0
        self.max_queue_length = 0

    def __eq__(self, other):

        return super().__eq__(other) and self.block == other.block

    @property
    def dscp(self):
        """DSCP code."""

        return self._dscp

    @dscp.setter
    def dscp(self, value):
        self._dscp = DSCP(value)

    @property
    def bins(self):
        """ Return the lvaps list """

        return self._bins

    @bins.setter
    def bins(self, bins):
        """ Setthe distribution bins. Default is [ 8192 ]."""

        if bins:

            if [x for x in bins if isinstance(x, int)] != bins:
                raise ValueError("bins values must be integers")

            if sorted(bins) != bins:
                raise ValueError("bins must be monotonically increasing")

            if sorted(set(bins)) != sorted(bins):
                raise ValueError("bins values must not contain duplicates")

            if [x for x in bins if x > 0] != bins:
                raise ValueError("bins values must be positive")

            self._bins = bins

        raise ValueError("empty bins")

    @property
    def block(self):
        """Block."""

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
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['bins'] = self.bins
        out['tx_bytes'] = self.tx_bytes
        out['tx_packets'] = self.tx_packets
        out['block'] = self.block.to_dict()
        out['dscp'] = self.dscp
        out['deficit_used'] = self.deficit_used
        out['max_queue_length'] = self.max_queue_length

        return out

    def run_once(self):
        """ Send out request. """

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

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        stats_req = Container(version=PT_VERSION,
                              type=PT_TRQ_BIN_COUNTER_REQUEST,
                              length=23+len(tenant.tenant_name),
                              seq=wtp.seq,
                              module_id=self.module_id,
                              hwaddr=self.block.hwaddr.to_raw(),
                              channel=self.block.channel,
                              band=self.block.band,
                              dscp=self.dscp.to_raw(),
                              ssid=tenant.tenant_name.to_raw())

        msg = TRQ_BIN_COUNTER_REQUEST.build(stats_req)
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
            if not entry:
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
            if not entry:
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

        self.deficit_used = response.deficit_used
        self.max_queue_length = response.max_queue_length

        # call callback
        self.handle_callback(self)


class TRQBinCounterWorker(ModuleLVAPPWorker):
    """Counter worker."""

    pass


def trq_bin_counter(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[TRQBinCounter.__module__]
    return worker.add_module(**kwargs)


def bound_trq_bin_counter(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return trq_bin_counter(**kwargs)


setattr(EmpowerApp, TRQBinCounter.MODULE_NAME, bound_trq_bin_counter)


def launch():
    """ Initialize the module. """

    return TRQBinCounterWorker(TRQBinCounter, PT_TRQ_BIN_COUNTER_RESPONSE,
                               TRQ_BIN_COUNTER_RESPONSE)
