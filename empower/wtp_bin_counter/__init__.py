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

"""WTP bin counter module."""

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


def get_module_id():
    """Get next next module id."""

    return RUNTIME.components["%s.wtp_bin_counter" % __name__].module_id


def register_callback(callback):
    """Regeister callback."""

    lvapp_server = RUNTIME.components[LVAPPServer.__module__]
    lvapp_server.register_message_handler(PT_WTP_STATS_RESPONSE, callback)


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
