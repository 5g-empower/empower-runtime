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

"""WiFi Channel Quality Map Worker."""

from construct import Struct, Int8ub, Int16ub, Int32ub, Bytes, Array
from construct import Container

import empower.managers.ranmanager.lvapp as lvapp

from empower.core.worker import EWorker
from empower.core.etheraddress import EtherAddress

PT_UCQM_REQUEST = 0x40
PT_UCQM_RESPONSE = 0x41

PT_NCQM_REQUEST = 0x42
PT_NCQM_RESPONSE = 0x43

CQM_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
)
CQM_REQUEST.name = "cqm_request"

CQM_ENTRY = Struct(
    "addr" / Bytes(6),
    "last_rssi_std" / Int8ub,
    "last_rssi_avg" / Int8ub,
    "last_packets" / Int32ub,
    "hist_packets" / Int32ub,
    "mov_rssi" / Int8ub
)
CQM_ENTRY.name = "ucqm_entry"

CQM_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "nb_entries" / Int16ub,
    "entries" / Array(lambda ctx: ctx.nb_entries, CQM_ENTRY)
)
CQM_RESPONSE.name = "cqm_response"


class ChannelQualityMap(EWorker):
    """WiFi Channel Quality Map Worker

    Parameters:
        service_id: the service id as an UUID (mandatory)
        every: the polling period in ms (optional, default: 2000)
    """

    def __init__(self, service_id, project_id, every):

        super().__init__(service_id=service_id,
                         project_id=project_id,
                         every=every)

        self.ucqm = {}
        self.ncqm = {}

        lvapp.register_message(PT_UCQM_REQUEST, CQM_REQUEST)
        lvapp.register_message(PT_UCQM_RESPONSE, CQM_RESPONSE)
        lvapp.register_message(PT_NCQM_REQUEST, CQM_REQUEST)
        lvapp.register_message(PT_NCQM_RESPONSE, CQM_RESPONSE)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = super().to_dict()

        output['ucqm'] = self.ucqm
        output['ncqm'] = self.ncqm

        return output

    def loop(self):
        """Send out requests"""

        for wtp in self.context.lvapp_manager.devices.values():

            if not wtp.connection:
                continue

            for block in wtp.blocks.values():

                msg = Container(length=CQM_REQUEST.sizeof(),
                                iface_id=block.block_id)

                wtp.connection.send_message(PT_UCQM_REQUEST,
                                            msg,
                                            self.handle_ucqm_response)

                wtp.connection.send_message(PT_NCQM_REQUEST,
                                            msg,
                                            self.handle_ncqm_response)

    def handle_ucqm_response(self, response, wtp, _):
        """Handle UCQM_RESPONSE message."""

        block = wtp.blocks[response.iface_id]
        block.ucqm = {}

        for entry in response.entries:
            addr = EtherAddress(entry['addr'])
            block.ucqm[addr] = {
                'addr': addr,
                'last_rssi_std': entry['last_rssi_std'],
                'last_rssi_avg': entry['last_rssi_avg'],
                'last_packets': entry['last_packets'],
                'hist_packets': entry['hist_packets'],
                'mov_rssi': entry['mov_rssi']
            }

        self.ucqm[block.block_id] = block.ucqm

        # handle callbacks
        self.handle_callbacks()

    def handle_ncqm_response(self, response, wtp, _):
        """Handle NCQM_RESPONSE message."""

        block = wtp.blocks[response.iface_id]
        block.ncqm = {}

        for entry in response.entries:
            addr = EtherAddress(entry['addr'])
            block.ncqm[addr] = {
                'addr': addr,
                'last_rssi_std': entry['last_rssi_std'],
                'last_rssi_avg': entry['last_rssi_avg'],
                'last_packets': entry['last_packets'],
                'hist_packets': entry['hist_packets'],
                'mov_rssi': entry['mov_rssi']
            }

        self.ncqm = block.ncqm

        # handle callbacks
        self.handle_callbacks()


def launch(service_id, project_id, every=2000):
    """ Initialize the module. """

    return ChannelQualityMap(service_id=service_id,
                             project_id=project_id,
                             every=every)
