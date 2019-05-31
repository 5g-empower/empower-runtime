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

""" WiFi Stats module. """

from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import Array

from datetime import datetime
from datetime import timedelta

from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import ModulePeriodic
from empower.core.resourcepool import ResourceBlock
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME

PT_WIFI_STATS_REQUEST = 0x37
PT_WIFI_STATS_RESPONSE = 0x38

ENTRY_TYPE = Sequence("entries",
                      UBInt8("type"),
                      UBInt32("timestamp"),
                      UBInt32("sample"))

WIFI_STATS_REQUEST = Struct("wifi_stats_request", UBInt8("version"),
                            UBInt8("type"),
                            UBInt32("length"),
                            UBInt32("seq"),
                            UBInt32("module_id"),
                            Bytes("hwaddr", 6),
                            UBInt8("channel"),
                            UBInt8("band"))

WIFI_STATS_RESPONSE = Struct("wifi_stats_response", UBInt8("version"),
                             UBInt8("type"),
                             UBInt32("length"),
                             UBInt32("seq"),
                             UBInt32("module_id"),
                             Bytes("wtp", 6),
                             UBInt16("nb_entries"),
                             Array(lambda ctx: ctx.nb_entries, ENTRY_TYPE))


class WiFiStats(ModulePeriodic):
    """Wi-Fi Stats."""

    MODULE_NAME = "wifi_stats"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    def __init__(self):

        super().__init__()

        # parameters
        self._block = None

        # data structures
        self.wifi_stats = {}
        self.agent_ts_ref = 0
        self.runtime_ts_ref = None
        self.last_runtime_ts = None
        self.tx_per_second = 0
        self.rx_per_second = 0
        self.ed_per_second = 0

    def __eq__(self, other):
        return super().__eq__(other) and self.block == other.block

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

        else:

            raise ValueError("Invalid block")

    def to_dict(self):
        """ Return a JSON-serializable dictionary. """

        out = super().to_dict()
        out['block'] = self.block.to_dict()
        out['wifi_stats'] = self.wifi_stats
        out['stats_per_second'] = {'tx_per_second': self.tx_per_second,
                                   'rx_per_second': self.rx_per_second,
                                   'ed_per_second': self.ed_per_second}

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

        req = Container(version=PT_VERSION,
                        type=PT_WIFI_STATS_REQUEST,
                        length=22,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, self.block, self.module_id)

        msg = WIFI_STATS_REQUEST.build(req)
        wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming poller response message.
        Args:
            message, a poller response message
        Returns:
            None
        """

        # update this object
        self.wifi_stats.clear()

        # pre-processing: ed = ed - (rx + tx)
        # tx: 0:100, rx: 100:200, ed: 200:300
        for index in range(200, 300):
            response.entries[index][2] -= (response.entries[index - 100][2]
                                           + response.entries[index - 200][2])

        # at the beginning, create the map between runtime and agent timestamps
        # entry[0] = stat type [0, 1, 2] -> [tx, rx, ed]
        # entry[1] = agent timestamp
        # entry[2] = stat value
        if self.agent_ts_ref == 0:
            for entry in response.entries:
                if entry[1] > self.agent_ts_ref:
                    self.agent_ts_ref = entry[1]
            self.runtime_ts_ref = datetime.utcnow()

        for entry in response.entries:

            stat_type = ["tx", "rx", "ed"][entry[0]]
            if stat_type not in self.wifi_stats:
                self.wifi_stats[stat_type] = []
            ts_delta = timedelta(microseconds=(entry[1] - self.agent_ts_ref))
            value = entry[2] / 180.0

            # skip invalid samples
            if abs(value) == 200:  # tx, rx: 200; ed: 200 - (200 + 200)
                continue

            sample = {
                "measurement": stat_type,
                "tags": {
                    "tenant": str(self.tenant_id),
                    "block": str(self._block)
                },
                "time": self.runtime_ts_ref + ts_delta,
                "fields": {
                    "value": value
                }
            }
            self.wifi_stats[stat_type].append(sample)

        if self.last_runtime_ts:
            self.tx_per_second = self.update_stats(self.wifi_stats['tx'])
            self.rx_per_second = self.update_stats(self.wifi_stats['rx'])
            self.ed_per_second = self.update_stats(self.wifi_stats['ed'])

        self.last_runtime_ts = datetime.utcnow()

        # update wifi_stats module
        self.block.wifi_stats = self.wifi_stats

        # call callback
        self.handle_callback(self)

        # update Influxdb
        self.update_db([sample for measurements in self.wifi_stats.values()
                        for sample in measurements])

    def update_stats(self, stats):
        """Update stats."""

        avg_sec = 0
        nb_samples = 0

        for sample in stats:
            if sample['time'] > self.last_runtime_ts:
                avg_sec += sample['fields']['value']
                nb_samples += 1

        if nb_samples == 0:
            return 0

        return avg_sec / nb_samples


class WiFiStatsWorker(ModuleLVAPPWorker):
    """ Counter worker. """

    pass


def wifi_stats(**kwargs):
    """Create a new module."""

    return RUNTIME.components[WiFiStatsWorker.__module__].add_module(**kwargs)


def bound_wifi_stats(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return wifi_stats(**kwargs)


setattr(EmpowerApp, WiFiStats.MODULE_NAME, bound_wifi_stats)


def launch():
    """ Initialize the module. """

    return WiFiStatsWorker(WiFiStats, PT_WIFI_STATS_RESPONSE,
                           WIFI_STATS_RESPONSE)
