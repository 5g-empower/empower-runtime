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

"""WiFi Rate Control Statistics Primitive."""

from datetime import datetime

from construct import Struct, Int8ub, Int16ub, Int32ub, Bytes, Array
from construct import Container

import empower.managers.ranmanager.lvapp as lvapp

from empower.core.ssid import WIFI_NWID_MAXSIZE
from empower.core.etheraddress import EtherAddress
from empower.managers.ranmanager.lvapp.wifiapp import EWiFiApp
from empower.core.app import EVERY


PT_WIFI_SLICE_STATS_REQUEST = 0x4C
PT_WIFI_SLICE_STATS_RESPONSE = 0x4D

WIFI_SLICE_STATS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1),
    "slice_id" / Int8ub,
)
WIFI_SLICE_STATS_REQUEST.name = "wifi_slice_stats_request"

SLICE_STATS_ENTRY = Struct(
    "iface_id" / Int32ub,
    "deficit_used" / Int32ub,
    "max_queue_length" / Int32ub,
    "tx_packets" / Int32ub,
    "tx_bytes" / Int32ub,
)
SLICE_STATS_ENTRY.name = "slice_stats_entry"

WIFI_SLICE_STATS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1),
    "slice_id" / Int8ub,
    "nb_entries" / Int16ub,
    "stats" / Array(lambda ctx: ctx.nb_entries, SLICE_STATS_ENTRY),
)
WIFI_SLICE_STATS_RESPONSE.name = "wifi_slice_stats_response"


class SliceStats(EWiFiApp):
    """WiFi Slice Statistics Primitive.

    This primitive collects the slice statistics.

    Parameters:
        slice_id: the slice to track (optinal, default 0)
        every: the loop period in ms (optional, default 2000ms)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.wifislicestats.wifislicestats",
            "params": {
                "slice_id": 0,
                "every": 2000
            }
        }
    """

    def __init__(self, context, service_id, slice_id, every=EVERY):

        super().__init__(context=context,
                         service_id=service_id,
                         slice_id=slice_id,
                         every=every)

        # Register messages
        lvapp.register_message(PT_WIFI_SLICE_STATS_REQUEST,
                               WIFI_SLICE_STATS_REQUEST)
        lvapp.register_message(PT_WIFI_SLICE_STATS_RESPONSE,
                               WIFI_SLICE_STATS_RESPONSE)

        # Data structures
        self.stats = {}

    def __eq__(self, other):
        if isinstance(other, HelloWorld):
            return self.slice_id == other.slice_id and \
                   self.every == other.every
        return False

    @property
    def slice_id(self):
        """ Return the slice_id """

        return self.params['slice_id']

    @slice_id.setter
    def slice_id(self, slice_id):
        """ Set the slice_id. """

        self.params['slice_id'] = int(slice_id)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = super().to_dict()

        out['slice_id'] = self.slice_id
        out['stats'] = self.stats

        return out

    def loop(self):
        """Send out requests"""

        for wtp in self.wtps.values():

            if not wtp.connection:
                continue

            msg = Container(length=WIFI_SLICE_STATS_REQUEST.sizeof(),
                            ssid=self.context.wifi_props.ssid.to_raw(),
                            slice_id=self.slice_id)

            wtp.connection.send_message(PT_WIFI_SLICE_STATS_REQUEST,
                                        msg,
                                        self.handle_response)

    def handle_response(self, response, *_):
        """Handle WIFI_SLICE_STATS_RESPONSE message."""

        wtp = EtherAddress(response.device)

        # update this object
        if wtp not in self.stats:
            self.stats[wtp] = {}

        # generate data points
        points = []
        timestamp = datetime.utcnow()

        for entry in response.stats:

            self.stats[wtp][entry.iface_id] = {
                'deficit_used': entry.deficit_used,
                'max_queue_length': entry.max_queue_length,
                'tx_packets': entry.tx_packets,
                'tx_bytes': entry.tx_bytes,
            }

            tags = dict(self.params)
            tags["wtp"] = wtp
            tags["iface_id"] = entry.iface_id

            sample = {
                "measurement": self.name,
                "tags": tags,
                "time": timestamp,
                "fields": self.stats[wtp][entry.iface_id]
            }

            points.append(sample)

        # save to db
        self.write_points(points)

        # handle callbacks
        self.handle_callbacks()


def launch(context, service_id, slice_id=0, every=EVERY):
    """ Initialize the module. """

    return SliceStats(context=context, service_id=service_id,
                      slice_id=slice_id, every=every)
