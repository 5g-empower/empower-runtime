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

"""WiFi Channel Statistics Worker."""

from datetime import datetime
from datetime import timedelta

from itertools import groupby

from construct import Struct, Int8ub, Int16ub, Int32ub, Int64ub, Bytes, Array
from construct import Container

import empower.managers.ranmanager.lvapp as lvapp

from empower.managers.ranmanager.lvapp.wifiworker import EWiFiWorker

PT_WCS_REQUEST = 0x4A
PT_WCS_RESPONSE = 0x4B

WCS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
)
WCS_REQUEST.name = "wcs_request"

WCS_ENTRY = Struct(
    "type" / Int8ub,
    "timestamp" / Int64ub,
    "sample" / Int32ub,
)
WCS_ENTRY.name = "wcs_entry"

WCS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "nb_entries" / Int16ub,
    "entries" / Array(lambda ctx: ctx.nb_entries, WCS_ENTRY)
)
WCS_RESPONSE.name = "wcs_response"


class ChannelStats(EWiFiWorker):
    """WiFi Channel Statistics Worker

    Parameters:
        every: the polling period in ms (optional, default: 2000)
    """

    def __init__(self, context, service_id, every):

        super().__init__(context=context, service_id=service_id, every=every)

        lvapp.register_message(PT_WCS_REQUEST, WCS_REQUEST)
        lvapp.register_message(PT_WCS_RESPONSE, WCS_RESPONSE)

        self.channel_stats = {}
        self.agent_ts_ref = {}
        self.runtime_ts_ref = {}

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = super().to_dict()

        output['channel_stats'] = self.channel_stats

        return output

    def loop(self):
        """Send out requests"""

        for wtp in self.context.wtps.values():

            if not wtp.connection:
                continue

            for block in wtp.blocks.values():

                msg = Container(length=WCS_REQUEST.sizeof(),
                                iface_id=block.block_id)

                wtp.connection.send_message(PT_WCS_REQUEST,
                                            msg,
                                            self.handle_response)

    def handle_response(self, response, wtp, _):
        """Handle WCS_RESPONSE message."""

        block_id = response.iface_id

        # init data structures for the incoming block
        if block_id not in self.channel_stats:
            self.channel_stats[block_id] = {}
            self.agent_ts_ref[block_id] = 0
            self.runtime_ts_ref[block_id] = None

        # pre-processing: ed = ed - (rx + tx)
        # tx: 0:100, rx: 100:200, ed: 200:300
        for index in range(200, 300):
            response.entries[index].sample -= \
                response.entries[index - 100].sample + \
                response.entries[index - 200].sample

        # at the beginning, create the map between runtime and agent timestamps
        # entry[0] = stat type [0, 1, 2] -> [tx, rx, ed]
        # entry[1] = agent timestamp
        # entry[2] = stat value
        if self.agent_ts_ref[block_id] == 0:
            for entry in response.entries:
                if entry.timestamp > self.agent_ts_ref[block_id]:
                    self.agent_ts_ref[block_id] = entry.timestamp
            self.runtime_ts_ref[block_id] = datetime.utcnow()

        self.channel_stats[block_id] = []

        for entry in response.entries:

            stat_type = ["tx", "rx", "ed"][entry.type]
            ts_delta = timedelta(microseconds=(entry.timestamp -
                                               self.agent_ts_ref[block_id]))
            value = entry.sample / 180.0

            # skip invalid samples
            if abs(value) == 200:  # tx, rx: 200; ed: 200 - (200 + 200)
                continue

            sample = {
                "type": stat_type,
                "time": self.runtime_ts_ref[block_id] + ts_delta,
                "value": value
            }

            self.channel_stats[block_id].append(sample)

        # update wifi_stats module
        block = wtp.blocks[block_id]
        block.channel_stats = self.channel_stats[block_id]

        # save samples
        sorted_samples = sorted(block.channel_stats,
                                key=lambda x: x["time"].timestamp())
        samples = []

        for tstamp, sample_fields in groupby(sorted_samples,
                                             lambda x: x["time"].timestamp()):

            fields = {}

            for item in sample_fields:
                fields[item["type"]] = item["value"]

            tags = dict(self.params)
            tags["wtp"] = wtp.addr
            tags["block_id"] = block_id

            sample = {
                "measurement": self.name,
                "tags": tags,
                "time": datetime.fromtimestamp(tstamp),
                "fields": fields
            }
            samples.append(sample)

        self.write_points(samples)

        # handle callbacks
        self.handle_callbacks()


def launch(context, service_id, every=2000):
    """ Initialize the module. """

    return ChannelStats(context=context, service_id=service_id, every=every)
