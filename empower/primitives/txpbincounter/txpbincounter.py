#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""TXP Bin Counter Primitive."""

import time
from datetime import datetime

from construct import Struct, Int8ub, Int16ub, Int32ub, Bytes, Array
from construct import Container

import empower.managers.ranmanager.lvapp as lvapp

from empower.core.etheraddress import EtherAddress
from empower.core.app import EApp
from empower.core.app import EVERY

PT_TXP_BIN_COUNTERS_REQUEST = 0x84
PT_TXP_BIN_COUNTERS_RESPONSE = 0x85

TXP_BIN_COUNTERS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "addr" / Bytes(6),
)
TXP_BIN_COUNTERS_REQUEST.name = "txp_bin_counters_request"

COUNTERS_ENTRY = Struct(
    "size" / Int16ub,
    "count" / Int32ub,
)
COUNTERS_ENTRY.name = "counters_entry"

TXP_BIN_COUNTERS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "addr" / Bytes(6),
    "nb_tx" / Int16ub,
    "stats" / Array(lambda ctx: ctx.nb_tx, COUNTERS_ENTRY),
)
TXP_BIN_COUNTERS_RESPONSE.name = "txp_bin_counters_response"


class TXPBinCounter(EApp):
    """TXP Bin Counter Primitive.

    This primitive collects the packet counters from the specified address.

    Parameters:
        service_id: the service id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)
        addr: the address to track as an EtherAddress (mandatory)
        bins: the bins for the measurements (optional, default: [8192])
        every: the loop period in ms (optional, default 2000ms)

    Callbacks:
        counters: called everytime new measurement is processed

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.lvapbincounter.lvapbincounter",
            "params": {
                "addr": "11:22:33:44:55:66",
                "every": 2000
            }
        }
    """

    def __init__(self, service_id, project_id, iface_id, addr, bins="8192",
                 every=EVERY):

        super().__init__(service_id=service_id,
                         project_id=project_id,
                         addr=addr,
                         iface_id=iface_id,
                         bins=bins,
                         every=every)

        # Register messages
        lvapp.register_message(PT_TXP_BIN_COUNTERS_REQUEST,
                               TXP_BIN_COUNTERS_REQUEST)

        lvapp.register_message(PT_TXP_BIN_COUNTERS_RESPONSE,
                               TXP_BIN_COUNTERS_RESPONSE)

        # Data structures
        self.counters = {
            "tx_packets": [],
            "tx_bytes": [],
            "tx_packets_per_second": [],
            "tx_bytes_per_second": [],
        }

        # Last seen time
        self.last = None

    @property
    def iface_id(self):
        """ Return the interface. """

        return self.params['iface_id']

    @iface_id.setter
    def iface_id(self, iface_id):
        """ Set the interface. """

        self.params['iface_id'] = int(iface_id)

    @property
    def addr(self):
        """ Return the station address. """

        return self.params['addr']

    @addr.setter
    def addr(self, addr):
        """ Set the station address. """

        self.params['addr'] = EtherAddress(addr)

    @property
    def bins(self):
        """ Return the bins. """

        return self.params['bins']

    @bins.setter
    def bins(self, bins):
        """ Set the bins. Default is [ 8192 ]. """

        if isinstance(bins, str):
            bins = [int(x) for x in bins.split(",")]

        if not isinstance(bins, list):
            raise ValueError("bins must be either a list of a string")

        if [x for x in bins if isinstance(x, int)] != bins:
            raise ValueError("bins values must be integers")

        if sorted(bins) != bins:
            raise ValueError("bins must be monotonically increasing")

        if sorted(set(bins)) != sorted(bins):
            raise ValueError("bins values must not contain duplicates")

        if [x for x in bins if x > 0] != bins:
            raise ValueError("bins values must be positive")

        self.params['bins'] = bins

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = super().to_dict()

        out['bins'] = self.bins
        out['addr'] = self.addr
        out['iface_id'] = self.iface_id
        out['counters'] = self.counters

        return out

    def loop(self):
        """Send out requests"""

        if self.addr not in self.context.lvaps:
            return

        lvap = self.context.lvaps[self.addr]

        msg = Container(length=TXP_BIN_COUNTERS_REQUEST.sizeof(),
                        iface_id=self.iface_id,
                        addr=lvap.addr.to_raw())

        lvap.wtp.connection.send_message(PT_TXP_BIN_COUNTERS_REQUEST,
                                         msg,
                                         self.handle_response)

    def fill_bytes_samples(self, data):
        """ Compute samples.

        Samples are in the following format (after ordering):

        [[60, 3], [66, 2], [74, 1], [98, 40], [167, 2], [209, 2], [1466, 1762]]

        Each 2-tuple has format [ size, count ] where count is the number of
        packets and size is the size-long (bytes, including the Ethernet 2
        header) TX/RX by the LVAP.
        """

        samples = sorted(data, key=lambda entry: entry.size)
        out = [0] * len(self.bins)

        for entry in samples:
            if not entry:
                continue
            for i in range(0, len(self.bins)):
                if entry.size <= self.bins[i]:
                    out[i] = out[i] + entry.size * entry.count
                    break

        return out

    def fill_packets_samples(self, data):
        """Compute samples.

        Samples are in the following format (after ordering):

        [[60, 3], [66, 2], [74, 1], [98, 40], [167, 2], [209, 2], [1466, 1762]]

        Each 2-tuple has format [ size, count ] where count is the number of
        packets and size is the size-long (bytes, including the Ethernet 2
        header) TX/RX by the LVAP.
        """

        samples = sorted(data, key=lambda entry: entry.size)
        out = [0] * len(self.bins)

        for entry in samples:
            if not entry:
                continue
            for i in range(0, len(self.bins)):
                if entry.size <= self.bins[i]:
                    out[i] = out[i] + entry.count
                    break

        return out

    @classmethod
    def update_stats(cls, delta, last, current):
        """Update stats."""

        stats = []

        for idx, _ in enumerate(last):
            diff = current[idx] - last[idx]
            stats.append(diff / delta)

        return stats

    def handle_response(self, response, *_):
        """Handle BIN_COUNTERS_RESPONSE message."""

        # update this object
        tx_samples = response.stats[0:response.nb_tx]
        old_tx_bytes = self.counters["tx_bytes"]
        old_tx_packets = self.counters["tx_packets"]

        self.counters["tx_bytes"] = self.fill_bytes_samples(tx_samples)
        self.counters["tx_packets"] = self.fill_packets_samples(tx_samples)

        self.counters["tx_bytes_per_second"] = [0.0] * len(self.bins)
        self.counters["tx_packets_per_second"] = [0.0] * len(self.bins)

        if self.last:
            delta = time.time() - self.last
            self.counters["tx_bytes_per_second"] = \
                self.update_stats(delta, old_tx_bytes,
                                  self.counters["tx_bytes"])
            self.counters["tx_packets_per_second"] = \
                self.update_stats(delta, old_tx_packets,
                                  self.counters["tx_packets"])

        # generate data points
        points = []

        for idx, _ in enumerate(self.bins):

            fields = {
                "addr": self.addr,
                "bin": self.bins[idx],
                "tx_bytes": self.counters["tx_bytes"][idx],
                "tx_packets": self.counters["tx_packets"][idx],
                "rx_bps": self.counters["rx_bps"][idx],
                "rx_pps": self.counters["rx_pps"][idx]
            }

            sample = {
                "measurement": self.name,
                "tags": self.params,
                "time": datetime.utcnow(),
                "fields": fields
            }

            points.append(sample)

        # save to db
        self.write_points(points)

        # handle callbacks
        self.handle_callbacks()

        # set last iteration time
        self.last = time.time()


def launch(service_id, project_id, iface_id, addr, bins="8192", every=EVERY):
    """ Initialize the module. """

    return TXPBinCounter(service_id=service_id, project_id=project_id,
                         iface_id=iface_id, addr=addr, bins=bins,
                         every=every)
