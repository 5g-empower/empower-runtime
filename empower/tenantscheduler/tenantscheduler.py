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

"""Tenant scheduler."""

import json
import tornado

from construct import UBInt8
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import UBInt16
from construct import UBInt32
from construct import Array

import empower.logger

from empower.lvapp import PT_VERSION
from empower.wtp_bin_counter.wtp_bin_counter import WTP_STATS_REQUEST
from empower.wtp_bin_counter.wtp_bin_counter import PT_WTP_STATS_RESPONSE
from empower.wtp_bin_counter.wtp_bin_counter import PT_WTP_STATS_REQUEST
from empower.lvapp.lvappserver import LVAPPServer
from empower.datatypes.etheraddress import EtherAddress

from empower.main import RUNTIME

DEFAULT_PERIOD = 5000


def send_stats_request(wtp, module_id=0):
    """Send stats request to specified WTP."""

    if not wtp.connection or wtp.connection.stream.closed():
        return

    stats_req = Container(version=PT_VERSION,
                          type=PT_WTP_STATS_REQUEST,
                          length=14,
                          seq=wtp.seq,
                          module_id=module_id)

    msg = WTP_STATS_REQUEST.build(stats_req)
    wtp.connection.stream.write(msg)


def parse_stats_response(response, bins=[8192]):
    """Parse stats response messge into the specified bins."""

    tx_samples = response.stats[0:response.nb_tx]
    rx_samples = response.stats[response.nb_tx:-1]

    out = {}

    out['wtp'] = EtherAddress(response.wtp)
    out['module_id'] = response.module_id
    out['tx_packets'] = fill_packets_sample(tx_samples, bins)
    out['rx_packets'] = fill_packets_sample(rx_samples, bins)
    out['tx_bytes'] = fill_bytes_sample(tx_samples, bins)
    out['rx_bytes'] = fill_bytes_sample(rx_samples, bins)

    return out


def fill_packets_sample(values, bins):

    out = {}

    for value in values:
        lvap = EtherAddress(value[0])
        if lvap not in out:
            out[lvap] = []
        out[lvap].append([value[1], value[2]])

    for lvap in out.keys():

        data = out[lvap]

        samples = sorted(data, key=lambda entry: entry[0])
        new_out = [0] * len(bins)

        for entry in samples:
            if len(entry) == 0:
                continue
            size = entry[0]
            count = entry[1]
            for i in range(0, len(bins)):
                if size <= bins[i]:
                    new_out[i] = new_out[i] + count
                    break

        out[lvap] = new_out

    return out


def fill_bytes_sample(values, bins):

    out = {}

    for value in values:
        lvap = EtherAddress(value[0])
        if lvap not in out:
            out[lvap] = []
        out[lvap].append([value[1], value[2]])

    for lvap in out.keys():

        data = out[lvap]

        samples = sorted(data, key=lambda entry: entry[0])
        new_out = [0] * len(bins)

        for entry in samples:
            if len(entry) == 0:
                continue
            size = entry[0]
            count = entry[1]
            for i in range(0, len(bins)):
                if size <= bins[i]:
                    new_out[i] = new_out[i] + size * count
                    break

        out[lvap] = new_out

    return out


class TenantScheduler():
    """Tenant Scheduler."""

    def __init__(self, every=DEFAULT_PERIOD):

        self.every = every
        self.log = empower.logger.get_logger()
        self.__worker = None
        self.wtp_bin_counter_module_id = 1
        self.wtps = {}

    def start(self):
        """Start control loop."""

        self.__worker = tornado.ioloop.PeriodicCallback(self.loop, self.every)
        self.__worker.start()

    def stop(self):
        """Stop control loop."""

        self.__worker.stop()

    def loop(self):
        """Control loop."""

        pass

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Stats """

        out = super().to_dict()

        out['wtps'] = {}

        for addr in self.wtps:
            out['wtps'][str(addr)] = \
                {str(k): v for k, v in self.wtps[addr].items()}

        return out

    def loop(self):
        """Periodic job."""

        self.log.info("Running tenants scheduler...")

        for tenant in RUNTIME.tenants.values():
            for wtp in tenant.wtps.values():
                send_stats_request(wtp, self.wtp_bin_counter_module_id)

    def handle_stats_response(self, stats):
        """Handle wtp bin counter response."""

        parsed = parse_stats_response(stats)

        if parsed['module_id'] != self.wtp_bin_counter_module_id:
            return

        self.log.info("Got stats response")


def launch(every=DEFAULT_PERIOD):
    """Start the Energino Server Module."""

    sched = TenantScheduler(every=every)

    lvapp_server = RUNTIME.components[LVAPPServer.__module__]
    lvapp_server.register_message_handler(PT_WTP_STATS_RESPONSE,
                                          sched.handle_stats_response)

    return sched
