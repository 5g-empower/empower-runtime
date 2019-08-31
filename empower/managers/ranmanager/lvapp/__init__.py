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

"""LVAPP protocols."""

from construct import Struct, Int8ub, Int16ub, Int32ub, Bytes, Array, \
    BitStruct, Padding, Flag, GreedyRange, BitsInteger

from empower.core.ssid import WIFI_NWID_MAXSIZE


PT_VERSION = 0x00

PT_DEVICE_DOWN = "device_down"
PT_DEVICE_UP = "device_up"
PT_CLIENT_JOIN = "client_join"
PT_CLIENT_LEAVE = "client_leave"

PT_HELLO_REQUEST = 0x01
PT_HELLO_RESPONSE = 0x02

PT_CAPS_REQUEST = 0x03
PT_CAPS_RESPONSE = 0x04

PT_PROBE_REQUEST = 0x05
PT_PROBE_RESPONSE = 0x06

PT_AUTH_REQUEST = 0x07
PT_AUTH_RESPONSE = 0x08

PT_ASSOC_REQUEST = 0x09
PT_ASSOC_RESPONSE = 0x0A

PT_ADD_LVAP_REQUEST = 0x0B
PT_ADD_LVAP_RESPONSE = 0x0C
PT_DEL_LVAP_REQUEST = 0x0D
PT_DEL_LVAP_RESPONSE = 0x0E
PT_LVAP_STATUS_RESPONSE = 0x0F
PT_LVAP_STATUS_REQUEST = 0x10

PT_ADD_VAP = 0x11
PT_DEL_VAP = 0x12
PT_VAP_STATUS_RESPONSE = 0x13
PT_VAP_STATUS_REQUEST = 0x14

PT_SET_TX_POLICY = 0x15
PT_DEL_TX_POLICY = 0x16
PT_TX_POLICY_STATUS_RESPONSE = 0x17
PT_TX_POLICY_STATUS_REQUEST = 0x18

PT_SET_SLICE = 0x19
PT_DEL_SLICE = 0x1A
PT_SLICE_STATUS_RESPONSE = 0x1B
PT_SLICE_STATUS_REQUEST = 0x1C

PT_IGMP_REPORT = 0xE0
PT_INCOMING_MCAST_ADDR = 0xE1

HEADER = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
HEADER.name = "header"

HELLO_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
HELLO_REQUEST.name = "hello_request"

HELLO_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
HELLO_RESPONSE.name = "hello_response"

CAPS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
CAPS_REQUEST.name = "caps_request"

CAPS_BLOCKS = Struct(
    "block_id" / Int8ub,
    "hwaddr" / Bytes(6),
    "channel" / Int8ub,
    "band" / Int8ub
)

CAPS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "nb_blocks" / Int8ub,
    "blocks" / Array(lambda ctx: ctx.nb_blocks, CAPS_BLOCKS),
)
CAPS_RESPONSE.name = "caps_response"

PROBE_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "sta" / Bytes(6),
    "flags" / BitStruct(
        "padding" / Padding(7),
        "ht_caps" / Flag
    ),
    "ht_caps_info" / BitStruct(
        "L_SIG_TXOP_Protection_Support" / Flag,
        "Forty_MHz_Intolerant" / Flag,
        "Reserved" / Flag,
        "DSSS_CCK_Mode_in_40_MHz" / Flag,
        "Maximum_AMSDU_Length" / Flag,
        "HT_Delayed_Block_Ack" / Flag,
        "Rx_STBC" / BitsInteger(2),
        "Tx_STBC" / Flag,
        "Short_GI_for_40_MHz" / Flag,
        "Short_GI_for_20_MHz" / Flag,
        "HT_Greenfield" / Flag,
        "SM_Power_Save" / BitsInteger(2),
        "Supported_Channel_Width_Set" / Flag,
        "LDPC_Coding_Capability" / Flag,
    ),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
PROBE_REQUEST.name = "probe_request"

PROBE_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
PROBE_RESPONSE.name = "probe_response"

AUTH_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
    "bssid" / Bytes(6)
)
AUTH_REQUEST.name = "auth_request"

AUTH_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6)
)
AUTH_RESPONSE.name = "auth_response"

ASSOC_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
    "flags" / BitStruct(
        "padding" / Padding(7),
        "ht_caps" / Flag
    ),
    "ht_caps_info" / BitStruct(
        "L_SIG_TXOP_Protection_Support" / Flag,
        "Forty_MHz_Intolerant" / Flag,
        "Reserved" / Flag,
        "DSSS_CCK_Mode_in_40_MHz" / Flag,
        "Maximum_AMSDU_Length" / Flag,
        "HT_Delayed_Block_Ack" / Flag,
        "Rx_STBC" / BitsInteger(2),
        "Tx_STBC" / Flag,
        "Short_GI_for_40_MHz" / Flag,
        "Short_GI_for_20_MHz" / Flag,
        "HT_Greenfield" / Flag,
        "SM_Power_Save" / BitsInteger(2),
        "Supported_Channel_Width_Set" / Flag,
        "LDPC_Coding_Capability" / Flag,
    ),
    "bssid" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
ASSOC_REQUEST.name = "assoc_request"

ASSOC_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6)
)
ASSOC_RESPONSE.name = "assoc_response"

ADD_LVAP_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "flags" / BitStruct(
        "padding" / Padding(4),
        "ht_caps" / Flag,
        "set_mask" / Flag,
        "associated" / Flag,
        "authenticated" / Flag
    ),
    "assoc_id" / Int16ub,
    "ht_caps_info" / BitStruct(
        "L_SIG_TXOP_Protection_Support" / Flag,
        "Forty_MHz_Intolerant" / Flag,
        "Reserved" / Flag,
        "DSSS_CCK_Mode_in_40_MHz" / Flag,
        "Maximum_AMSDU_Length" / Flag,
        "HT_Delayed_Block_Ack" / Flag,
        "Rx_STBC" / BitsInteger(2),
        "Tx_STBC" / Flag,
        "Short_GI_for_40_MHz" / Flag,
        "Short_GI_for_20_MHz" / Flag,
        "HT_Greenfield" / Flag,
        "SM_Power_Save" / BitsInteger(2),
        "Supported_Channel_Width_Set" / Flag,
        "LDPC_Coding_Capability" / Flag,
    ),
    "sta" / Bytes(6),
    "encap" / Bytes(6),
    "bssid" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1),
    "networks" / GreedyRange(
        Struct(
            "bssid" / Bytes(6),
            "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1),
        )
    )
)
ADD_LVAP_REQUEST.name = "add_lvap_request"

ADD_LVAP_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
    "status" / Int32ub
)
ADD_LVAP_RESPONSE.name = "add_lvap_response"

DEL_LVAP_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
    "csa_switch_mode" / Int8ub,
    "csa_switch_count" / Int8ub,
    "csa_switch_channel" / Int8ub
)
DEL_LVAP_REQUEST.name = "del_lvap_request"

DEL_LVAP_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
    "status" / Int32ub
)
DEL_LVAP_RESPONSE.name = "del_lvap_response"

LVAP_STATUS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
LVAP_STATUS_REQUEST.name = "lvap_status_request"

LVAP_STATUS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "flags" / BitStruct(
        "padding" / Padding(4),
        "ht_caps" / Flag,
        "set_mask" / Flag,
        "associated" / Flag,
        "authenticated" / Flag
    ),
    "assoc_id" / Int16ub,
    "ht_caps_info" / BitStruct(
        "L_SIG_TXOP_Protection_Support" / Flag,
        "Forty_MHz_Intolerant" / Flag,
        "Reserved" / Flag,
        "DSSS_CCK_Mode_in_40_MHz" / Flag,
        "Maximum_AMSDU_Length" / Flag,
        "HT_Delayed_Block_Ack" / Flag,
        "Rx_STBC" / BitsInteger(2),
        "Tx_STBC" / Flag,
        "Short_GI_for_40_MHz" / Flag,
        "Short_GI_for_20_MHz" / Flag,
        "HT_Greenfield" / Flag,
        "SM_Power_Save" / BitsInteger(2),
        "Supported_Channel_Width_Set" / Flag,
        "LDPC_Coding_Capability" / Flag,
    ),
    "sta" / Bytes(6),
    "encap" / Bytes(6),
    "bssid" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1),
    "networks" / GreedyRange(
        Struct(
            "bssid" / Bytes(6),
            "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1),
        )
    )
)
LVAP_STATUS_RESPONSE.name = "lvap_status_response"

ADD_VAP = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "bssid" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
ADD_VAP.name = "add_vap"

DEL_VAP = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "bssid" / Bytes(6)
)
DEL_VAP.name = "del_vap"

VAP_STATUS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
VAP_STATUS_REQUEST.name = "vap_status_request"

VAP_STATUS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "bssid" / Bytes(6),
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
VAP_STATUS_RESPONSE.name = "vap_status_response"

SET_TX_POLICY = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "flags" / BitStruct(
        "padding" / Padding(7),
        "no_ack" / Flag
    ),
    "sta" / Bytes(6),
    "rts_cts" / Int16ub,
    "max_amsdu_len" / Int16ub,
    "tx_mcast" / Int8ub,
    "ur_count" / Int8ub,
    "nb_mcses" / Int8ub,
    "nb_ht_mcses" / Int8ub,
    "mcs" / Array(lambda ctx: ctx.nb_mcses, Int8ub),
    "mcs_ht" / Array(lambda ctx: ctx.nb_ht_mcses, Int8ub)
)
SET_TX_POLICY.name = "set_tx_policy"

DEL_TX_POLICY = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "sta" / Bytes(6)
)
DEL_TX_POLICY.name = "del_tx_policy"

TX_POLICY_STATUS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
TX_POLICY_STATUS_REQUEST.name = "tx_policy_status_request"

TX_POLICY_STATUS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "flags" / BitStruct(
        "padding" / Padding(7),
        "no_ack" / Flag
    ),
    "sta" / Bytes(6),
    "rts_cts" / Int16ub,
    "max_amsdu_len" / Int16ub,
    "tx_mcast" / Int8ub,
    "ur_count" / Int8ub,
    "nb_mcses" / Int8ub,
    "nb_ht_mcses" / Int8ub,
    "mcs" / Array(lambda ctx: ctx.nb_mcses, Int8ub),
    "mcs_ht" / Array(lambda ctx: ctx.nb_ht_mcses, Int8ub)
)
TX_POLICY_STATUS_RESPONSE.name = "tx_policy_status_response"

SET_SLICE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "slice_id" / Int8ub,
    "sta_scheduler" / Int8ub,
    "flags" / BitStruct(
        "padding" / Padding(7),
        "amsdu_aggregation" / Flag
    ),
    "quantum" / Int32ub,
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
SET_SLICE.name = "set_slice"

DEL_SLICE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "slice_id" / Int8ub,
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
DEL_SLICE.name = "del_slice"

SLICE_STATUS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
)
SLICE_STATUS_REQUEST.name = "slice_status_request"

SLICE_STATUS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "slice_id" / Int8ub,
    "sta_scheduler" / Int8ub,
    "flags" / BitStruct(
        "padding" / Padding(7),
        "amsdu_aggregation" / Flag
    ),
    "quantum" / Int32ub,
    "ssid" / Bytes(WIFI_NWID_MAXSIZE + 1)
)
SLICE_STATUS_RESPONSE.name = "slice_status_response"

IGMP_REPORT = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
    "mcast_addr" / Bytes(4),
    "igmp_type" / Int8ub
)
IGMP_REPORT.name = "igmp_report"

INCOMING_MCAST_ADDR = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "mcast_addr" / Bytes(6),
)
INCOMING_MCAST_ADDR.name = "incoming_mcast_address"

PT_TYPES = {

    PT_DEVICE_DOWN: None,
    PT_DEVICE_UP: None,
    PT_CLIENT_JOIN: None,
    PT_CLIENT_LEAVE: None,

    PT_HELLO_REQUEST: HELLO_REQUEST,
    PT_HELLO_RESPONSE: HELLO_RESPONSE,

    PT_CAPS_RESPONSE: CAPS_RESPONSE,
    PT_CAPS_REQUEST: CAPS_REQUEST,

    PT_PROBE_REQUEST: PROBE_REQUEST,
    PT_PROBE_RESPONSE: PROBE_RESPONSE,

    PT_AUTH_REQUEST: AUTH_REQUEST,
    PT_AUTH_RESPONSE: AUTH_RESPONSE,

    PT_ASSOC_REQUEST: ASSOC_REQUEST,
    PT_ASSOC_RESPONSE: ASSOC_RESPONSE,

    PT_ADD_LVAP_REQUEST: ADD_LVAP_REQUEST,
    PT_ADD_LVAP_RESPONSE: ADD_LVAP_RESPONSE,

    PT_DEL_LVAP_REQUEST: DEL_LVAP_REQUEST,
    PT_DEL_LVAP_RESPONSE: DEL_LVAP_RESPONSE,

    PT_LVAP_STATUS_REQUEST: LVAP_STATUS_REQUEST,
    PT_LVAP_STATUS_RESPONSE: LVAP_STATUS_RESPONSE,

    PT_ADD_VAP: ADD_VAP,
    PT_DEL_VAP: DEL_VAP,

    PT_VAP_STATUS_REQUEST: VAP_STATUS_REQUEST,
    PT_VAP_STATUS_RESPONSE: VAP_STATUS_RESPONSE,

    PT_TX_POLICY_STATUS_REQUEST: TX_POLICY_STATUS_REQUEST,
    PT_TX_POLICY_STATUS_RESPONSE: TX_POLICY_STATUS_RESPONSE,
    PT_SET_TX_POLICY: SET_TX_POLICY,
    PT_DEL_TX_POLICY: DEL_TX_POLICY,

    PT_SLICE_STATUS_REQUEST: SLICE_STATUS_REQUEST,
    PT_SLICE_STATUS_RESPONSE: SLICE_STATUS_RESPONSE,
    PT_SET_SLICE: SET_SLICE,
    PT_DEL_SLICE: DEL_SLICE,

    PT_IGMP_REPORT: IGMP_REPORT,
    PT_INCOMING_MCAST_ADDR: INCOMING_MCAST_ADDR

}


PT_TYPES_HANDLERS = {}

for k in PT_TYPES:
    PT_TYPES_HANDLERS[k] = []


def register_message(pt_type, parser):
    """Register new message and a new handler."""

    if pt_type not in PT_TYPES:
        PT_TYPES[pt_type] = parser

    if pt_type not in PT_TYPES_HANDLERS:
        PT_TYPES_HANDLERS[pt_type] = []


def register_callback(pt_type, handler):
    """Register new message and a new handler."""

    if pt_type not in PT_TYPES:
        raise KeyError("Packet type %u undefined")

    if pt_type not in PT_TYPES_HANDLERS:
        PT_TYPES_HANDLERS[pt_type] = []

    PT_TYPES_HANDLERS[pt_type].append(handler)


def unregister_callback(pt_type, handler):
    """Register new message and a new handler."""

    if pt_type not in PT_TYPES:
        raise KeyError("Packet type %u undefined")

    if pt_type not in PT_TYPES_HANDLERS:
        return

    PT_TYPES_HANDLERS[pt_type].remove(handler)
