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

"""Common counters module."""

from construct import UBInt8
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import UBInt16
from construct import UBInt32
from construct import Array

from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import Module
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME


PT_STATS_REQUEST = 0x17
PT_STATS_RESPONSE = 0x18

STATS = Sequence("stats", UBInt16("bytes"), UBInt32("count"))

STATS_REQUEST = Struct("stats_request", UBInt8("version"),
                       UBInt8("type"),
                       UBInt16("length"),
                       UBInt32("seq"),
                       UBInt32("module_id"),
                       Bytes("sta", 6))

STATS_RESPONSE = \
    Struct("stats_response", UBInt8("version"),
           UBInt8("type"),
           UBInt16("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("wtp", 6),
           Bytes("sta", 6),
           UBInt16("nb_tx"),
           UBInt16("nb_rx"),
           Array(lambda ctx: ctx.nb_tx + ctx.nb_rx, STATS))


class Counter(Module):
    """ PacketsCounter object. """

    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvap']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._lvap = None
        self._bins = [8192]

        # data structures
        self._tx_samples = []
        self._rx_samples = []

    def __eq__(self, other):

        return super().__eq__(other) and self.lvap == other.lvap and \
            self.bins == other.bins

    @property
    def lvap(self):
        return self._lvap

    @lvap.setter
    def lvap(self, value):
        self._lvap = EtherAddress(value)

    def fill_samples(self, data):
        pass

    @property
    def tx_samples(self):
        return self.fill_samples(self._tx_samples)

    @tx_samples.setter
    def tx_samples(self, value):
        self._tx_samples = value

    @property
    def rx_samples(self):
        return self.fill_samples(self._rx_samples)

    @rx_samples.setter
    def rx_samples(self, value):
        self._rx_samples = value

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
        out['tx'] = self.tx_samples
        out['rx'] = self.rx_samples

        return out

    def run_once(self):
        """ Send out stats request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.unload()
            return

        lvaps = RUNTIME.tenants[self.tenant_id].lvaps

        if self.lvap not in lvaps:
            self.unload()
            return

        lvap = lvaps[self.lvap]

        if not lvap.wtp.connection:
            self.unload()
            return

        stats_req = Container(version=PT_VERSION,
                              type=PT_STATS_REQUEST,
                              length=18,
                              seq=lvap.wtp.seq,
                              module_id=self.module_id,
                              sta=lvap.addr.to_raw())

        self.log.info("Sending stats request to %s @ %s (id=%u)",
                      lvap.addr, lvap.wtp.addr, self.module_id)

        msg = STATS_REQUEST.build(stats_req)
        lvap.wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming STATS_RESPONSE message.
        Args:
            stats, a STATS_RESPONSE message
        Returns:
            None
        """

        # update cache
        lvap = RUNTIME.lvaps[self.lvap]
        lvap.tx_samples = response.stats[0:response.nb_tx]
        lvap.rx_samples = response.stats[response.nb_tx:-1]

        # update this object
        self.tx_samples = response.stats[0:response.nb_tx]
        self.rx_samples = response.stats[response.nb_tx:-1]

        # call callback
        self.handle_callback(self)
