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

""" LVAPP Server module. """

from construct import Sequence
from construct import Array
from construct import Struct
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import Range
from construct import BitStruct
from construct import Bit
from construct import Padding
from construct import OptionalGreedyRange
from construct import Rename
from empower.datatypes.ssid import WIFI_NWID_MAXSIZE


PT_VERSION = 0x00

PT_BYE = "bye"
PT_REGISTER = "register"
PT_LVAP_JOIN = "lvap_join"
PT_LVAP_LEAVE = "lvap_leave"
PT_LVAP_HANDOVER = "lvap_handover"

PT_HELLO = 0x04
PT_PROBE_REQUEST = 0x05
PT_PROBE_RESPONSE = 0x06
PT_AUTH_REQUEST = 0x07
PT_AUTH_RESPONSE = 0x08
PT_ASSOC_REQUEST = 0x09
PT_ASSOC_RESPONSE = 0x10
PT_ADD_LVAP = 0x11
PT_DEL_LVAP = 0x12
PT_STATUS_LVAP = 0x13
PT_SET_TRANSMISSION_POLICY = 0x14
PT_DEL_TRANSMISSION_POLICY = 0x80
PT_STATUS_TRANSMISSION_POLICY = 0x15
PT_TRANSMISSION_POLICY_STATUS_REQUEST = 0x62
PT_CAPS_REQUEST = 0x16
PT_CAPS_RESPONSE = 0x17
PT_ADD_VAP = 0x32
PT_DEL_VAP = 0x33
PT_STATUS_VAP = 0x34
PT_ADD_LVAP_RESPONSE = 0x51
PT_DEL_LVAP_RESPONSE = 0x52
PT_LVAP_STATUS_REQUEST = 0x53
PT_VAP_STATUS_REQUEST = 0x54
PT_SET_SLICE = 0x56
PT_DEL_SLICE = 0x57
PT_STATUS_SLICE = 0x58
PT_SLICE_STATUS_REQUEST = 0x61
PT_IGMP_REPORT = 0x48
PT_INCOMING_MCAST_ADDR = 0x46

HEADER = Struct("header", UBInt8("version"),
                UBInt8("type"),
                UBInt32("length"))

HELLO = Struct("hello", UBInt8("version"),
               UBInt8("type"),
               UBInt32("length"),
               UBInt32("seq"),
               Bytes("wtp", 6),
               UBInt32("period"))

PROBE_REQUEST = Struct("probe_request", UBInt8("version"),
                       UBInt8("type"),
                       UBInt32("length"),
                       UBInt32("seq"),
                       Bytes("wtp", 6),
                       Bytes("sta", 6),
                       Bytes("hwaddr", 6),
                       UBInt8("channel"),
                       UBInt8("band"),
                       UBInt8("supported_band"),
                       Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

PROBE_RESPONSE = Struct("probe_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt32("length"),
                        UBInt32("seq"),
                        Bytes("sta", 6),
                        Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

AUTH_REQUEST = Struct("auth_request", UBInt8("version"),
                      UBInt8("type"),
                      UBInt32("length"),
                      UBInt32("seq"),
                      Bytes("wtp", 6),
                      Bytes("sta", 6),
                      Bytes("bssid", 6))

AUTH_RESPONSE = Struct("auth_response", UBInt8("version"),
                       UBInt8("type"),
                       UBInt32("length"),
                       UBInt32("seq"),
                       Bytes("sta", 6))

ASSOC_REQUEST = \
    Struct("assoc_request", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           Bytes("wtp", 6),
           Bytes("sta", 6),
           Bytes("bssid", 6),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           UBInt8("supported_band"),
           Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

ASSOC_RESPONSE = Struct("assoc_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt32("length"),
                        UBInt32("seq"),
                        Bytes("sta", 6))

NETWORKS = Struct("networks",
                  Bytes("bssid", 6),
                  Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

ADD_LVAP = Struct("add_lvap", UBInt8("version"),
                  UBInt8("type"),
                  UBInt32("length"),
                  UBInt32("seq"),
                  UBInt32("module_id"),
                  BitStruct("flags", Padding(13),
                            Bit("set_mask"),
                            Bit("associated"),
                            Bit("authenticated")),
                  UBInt16("assoc_id"),
                  Bytes("hwaddr", 6),
                  UBInt8("channel"),
                  UBInt8("band"),
                  UBInt8("supported_band"),
                  Bytes("sta", 6),
                  Bytes("encap", 6),
                  Bytes("bssid", 6),
                  Bytes("ssid", WIFI_NWID_MAXSIZE + 1),
                  Rename("networks", OptionalGreedyRange(NETWORKS)))

DEL_LVAP = Struct("del_lvap", UBInt8("version"),
                  UBInt8("type"),
                  UBInt32("length"),
                  UBInt32("seq"),
                  UBInt32("module_id"),
                  Bytes("sta", 6),
                  UBInt8("csa_switch_mode"),
                  UBInt8("csa_switch_count"),
                  UBInt8("csa_switch_channel"))

STATUS_LVAP = Struct("status_lvap", UBInt8("version"),
                     UBInt8("type"),
                     UBInt32("length"),
                     UBInt32("seq"),
                     BitStruct("flags", Padding(13),
                               Bit("set_mask"),
                               Bit("associated"),
                               Bit("authenticated")),
                     UBInt16("assoc_id"),
                     Bytes("wtp", 6),
                     Bytes("sta", 6),
                     Bytes("encap", 6),
                     Bytes("hwaddr", 6),
                     UBInt8("channel"),
                     UBInt8("band"),
                     UBInt8("supported_band"),
                     Bytes("bssid", 6),
                     Bytes("ssid", WIFI_NWID_MAXSIZE + 1),
                     Rename("networks", OptionalGreedyRange(NETWORKS)))

CAPS_R = Sequence("blocks",
                  Bytes("hwaddr", 6),
                  UBInt8("channel"),
                  UBInt8("band"))

CAPS_P = Sequence("ports", Bytes("hwaddr", 6),
                  UBInt16("port_id"),
                  Bytes("iface", 10))

CAPS_RESPONSE = Struct("caps", UBInt8("version"),
                       UBInt8("type"),
                       UBInt32("length"),
                       UBInt32("seq"),
                       Bytes("wtp", 6),
                       Bytes("dpid", 8),
                       UBInt8("nb_resources_elements"),
                       UBInt8("nb_ports_elements"),
                       Array(lambda ctx: ctx.nb_resources_elements, CAPS_R),
                       Array(lambda ctx: ctx.nb_ports_elements, CAPS_P))

CAPS_REQUEST = Struct("caps_request", UBInt8("version"),
                      UBInt8("type"),
                      UBInt32("length"),
                      UBInt32("seq"))

LVAP_STATUS_REQUEST = Struct("lvap_status_request", UBInt8("version"),
                             UBInt8("type"),
                             UBInt32("length"),
                             UBInt32("seq"))

SLICE_STATUS_REQUEST = \
    Struct("slice_status_request", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"))

TRANSMISSION_POLICY_STATUS_REQUEST = \
    Struct("transmission_policy_status_request", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"))

VAP_STATUS_REQUEST = Struct("vap_status_request", UBInt8("version"),
                            UBInt8("type"),
                            UBInt32("length"),
                            UBInt32("seq"))

SET_TRANSMISSION_POLICY = \
    Struct("set_transmission_policy", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           BitStruct("flags", Padding(15),
                     Bit("no_ack")),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           Bytes("sta", 6),
           UBInt16("rts_cts"),
           UBInt8("tx_mcast"),
           UBInt8("ur_mcast_count"),
           UBInt8("nb_mcses"),
           UBInt8("nb_ht_mcses"),
           Array(lambda ctx: ctx.nb_mcses, UBInt8("mcs")),
           Array(lambda ctx: ctx.nb_ht_mcses, UBInt8("ht_mcs")))

DEL_TRANSMISSION_POLICY = \
    Struct("del_transmission_policy", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           Bytes("sta", 6))

STATUS_TRANSMISSION_POLICY = \
    Struct("status_transmission_policy",
           UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           BitStruct("flags", Padding(15),
                     Bit("no_ack")),
           Bytes("wtp", 6),
           Bytes("sta", 6),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           UBInt16("rts_cts"),
           UBInt8("tx_mcast"),
           UBInt8("ur_mcast_count"),
           UBInt8("nb_mcses"),
           UBInt8("nb_ht_mcses"),
           Array(lambda ctx: ctx.nb_mcses, UBInt8("mcs")),
           Array(lambda ctx: ctx.nb_ht_mcses, UBInt8("ht_mcs")))

ADD_VAP = Struct("add_vap", UBInt8("version"),
                 UBInt8("type"),
                 UBInt32("length"),
                 UBInt32("seq"),
                 Bytes("hwaddr", 6),
                 UBInt8("channel"),
                 UBInt8("band"),
                 Bytes("bssid", 6),
                 Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

DEL_VAP = Struct("del_vap", UBInt8("version"),
                 UBInt8("type"),
                 UBInt32("length"),
                 UBInt32("seq"),
                 Bytes("bssid", 6))

STATUS_VAP = Struct("status_vap", UBInt8("version"),
                    UBInt8("type"),
                    UBInt32("length"),
                    UBInt32("seq"),
                    Bytes("wtp", 6),
                    Bytes("hwaddr", 6),
                    UBInt8("channel"),
                    UBInt8("band"),
                    Bytes("bssid", 6),
                    Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

ADD_LVAP_RESPONSE = Struct("add_lvap_response", UBInt8("version"),
                           UBInt8("type"),
                           UBInt32("length"),
                           UBInt32("seq"),
                           Bytes("wtp", 6),
                           Bytes("sta", 6),
                           UBInt32("module_id"),
                           UBInt32("status"))

DEL_LVAP_RESPONSE = Struct("del_lvap_response", UBInt8("version"),
                           UBInt8("type"),
                           UBInt32("length"),
                           UBInt32("seq"),
                           Bytes("wtp", 6),
                           Bytes("sta", 6),
                           UBInt32("module_id"),
                           UBInt32("status"))

SET_SLICE = \
    Struct("set_slice",
           UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           BitStruct("flags", Padding(15),
                     Bit("amsdu_aggregation")),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           UBInt32("quantum"),
           UBInt8("dscp"),
           Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

DEL_SLICE = \
    Struct("del_slice",
           UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           UBInt8("dscp"),
           Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

STATUS_SLICE = \
    Struct("status_slice",
           UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           Bytes("wtp", 6),
           BitStruct("flags", Padding(15),
                     Bit("amsdu_aggregation")),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           UBInt32("quantum"),
           UBInt8("dscp"),
           Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

IGMP_REPORT = Struct("igmp_report", UBInt8("version"),
                     UBInt8("type"),
                     UBInt32("length"),
                     UBInt32("seq"),
                     Bytes("wtp", 6),
                     Bytes("sta", 6),
                     Bytes("mcast_addr", 4),
                     UBInt8("igmp_type"))

INCOMING_MCAST_ADDR = Struct("incoming_mcast_address", UBInt8("version"),
                             UBInt8("type"),
                             UBInt32("length"),
                             UBInt32("seq"),
                             Bytes("wtp", 6),
                             Bytes("mcast_addr", 6),
                             Bytes("hwaddr", 6),
                             UBInt8("channel"),
                             UBInt8("band"))

PT_TYPES = {PT_BYE: None,
            PT_REGISTER: None,
            PT_LVAP_JOIN: None,
            PT_LVAP_LEAVE: None,
            PT_LVAP_HANDOVER: None,
            PT_HELLO: HELLO,
            PT_PROBE_REQUEST: PROBE_REQUEST,
            PT_PROBE_RESPONSE: PROBE_RESPONSE,
            PT_AUTH_REQUEST: AUTH_REQUEST,
            PT_AUTH_RESPONSE: AUTH_RESPONSE,
            PT_ASSOC_REQUEST: ASSOC_REQUEST,
            PT_ASSOC_RESPONSE: ASSOC_RESPONSE,
            PT_ADD_LVAP: ADD_LVAP,
            PT_DEL_LVAP: DEL_LVAP,
            PT_ADD_VAP: ADD_VAP,
            PT_DEL_VAP: DEL_VAP,
            PT_STATUS_LVAP: STATUS_LVAP,
            PT_CAPS_RESPONSE: CAPS_RESPONSE,
            PT_CAPS_REQUEST: CAPS_REQUEST,
            PT_TRANSMISSION_POLICY_STATUS_REQUEST:
                TRANSMISSION_POLICY_STATUS_REQUEST,
            PT_SET_TRANSMISSION_POLICY: SET_TRANSMISSION_POLICY,
            PT_DEL_TRANSMISSION_POLICY: DEL_TRANSMISSION_POLICY,
            PT_STATUS_TRANSMISSION_POLICY: STATUS_TRANSMISSION_POLICY,
            PT_STATUS_VAP: STATUS_VAP,
            PT_LVAP_STATUS_REQUEST: LVAP_STATUS_REQUEST,
            PT_VAP_STATUS_REQUEST: VAP_STATUS_REQUEST,
            PT_ADD_LVAP_RESPONSE: ADD_LVAP_RESPONSE,
            PT_DEL_LVAP_RESPONSE: DEL_LVAP_RESPONSE,
            PT_SLICE_STATUS_REQUEST: SLICE_STATUS_REQUEST,
            PT_STATUS_SLICE: STATUS_SLICE,
            PT_SET_SLICE: SET_SLICE,
            PT_DEL_SLICE: DEL_SLICE,
            PT_IGMP_REPORT: IGMP_REPORT,
            PT_INCOMING_MCAST_ADDR: INCOMING_MCAST_ADDR}


PT_TYPES_HANDLERS = {}
for k in PT_TYPES:
    PT_TYPES_HANDLERS[k] = []
