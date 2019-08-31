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

"""WiFi Slice Statistics Worker."""

from construct import Struct, Int8ub, Int16ub, Int32ub, Bytes, Array
from construct import Container

import empower.managers.ranmanager.lvapp as lvapp
from empower.core.ssid import WIFI_NWID_MAXSIZE
from empower.core.ssid import SSID

from empower.core.worker import EWorker

PT_WSS_REQUEST = 0x4C
PT_WSS_RESPONSE = 0x4D

WSS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
)
WSS_REQUEST.name = "wss_request"

WSS_ENTRY = Struct(
    "slice_id" / Int8ub,
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1),
    "deficit_used" / Int32ub,
    "max_queue_length" / Int32ub,
    "tx_packets" / Int32ub,
    "tx_bytes" / Int32ub,
)
WSS_ENTRY.name = "wss_entry"

WSS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "nb_entries" / Int16ub,
    "entries" / Array(lambda ctx: ctx.nb_entries, WSS_ENTRY)
)
WSS_RESPONSE.name = "wss_response"


class SliceStats(EWorker):
    """WiFi Slice Statistics Worker.

    Parameters:
        service_id: the service id as an UUID (mandatory)
        every: the polling period in ms (optional, default: 2000)
    """

    def __init__(self, service_id, project_id, every):

        super().__init__(service_id=service_id,
                         project_id=project_id,
                         every=every)

        lvapp.register_message(PT_WSS_REQUEST, WSS_REQUEST)
        lvapp.register_message(PT_WSS_RESPONSE, WSS_RESPONSE)

        self.slice_stats = {}

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = super().to_dict()

        output['slice_stats'] = self.slice_stats

        return output

    def loop(self):
        """Send out requests"""

        for wtp in self.context.lvapp_manager.devices.values():

            if not wtp.connection:
                continue

            for block in wtp.blocks.values():

                msg = Container(length=WSS_REQUEST.sizeof(),
                                iface_id=block.block_id)

                wtp.connection.send_message(PT_WSS_REQUEST,
                                            msg,
                                            self.handle_response)

    def handle_response(self, response, wtp, _):
        """Handle WSS_RESPONSE message."""

        block_id = response.iface_id

        # init data structures for the incoming block
        self.slice_stats[block_id] = {}

        for entry in response.entries:

            ssid = SSID(entry.ssid)

            if str(ssid) not in self.slice_stats[block_id]:
                self.slice_stats[block_id][str(ssid)] = {}

            self.slice_stats[block_id][str(ssid)][entry.slice_id] = {
                "deficit_used": entry.deficit_used,
                "max_queue_length": entry.max_queue_length,
                "tx_packets": entry.tx_packets,
                "tx_bytes": entry.tx_bytes,
            }

        # update wifi_stats module
        block = wtp.blocks[block_id]
        block.slice_stats = self.slice_stats[block_id]

        # handle callbacks
        self.handle_callbacks("slice_stats")


def launch(service_id, project_id, every=2000):
    """ Initialize the module. """

    return SliceStats(service_id=service_id,
                      project_id=project_id,
                      every=every)
