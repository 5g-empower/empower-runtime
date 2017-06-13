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


PT_VERSION = 0x00

PT_BYE = 0x00
PT_REGISTER = 0x01
PT_LVAP_JOIN = 0x02
PT_LVAP_LEAVE = 0x03
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
PT_SET_PORT = 0x14
PT_STATUS_PORT = 0x15
PT_CAPS = 0x16
PT_ADD_VAP = 0x31
PT_DEL_VAP = 0x32
PT_STATUS_VAP = 0x33

HEADER = Struct("header", UBInt8("version"),
                UBInt8("type"),
                UBInt32("length"))

SSIDS = Range(1, 10, Struct("ssids", UBInt8("length"),
                            Bytes("ssid", lambda ctx: ctx.length)))

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
                       Bytes("ssid", lambda ctx: ctx.length - 30))

PROBE_RESPONSE = Struct("probe_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt32("length"),
                        UBInt32("seq"),
                        Bytes("sta", 6))

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
           Bytes("ssid", lambda ctx: ctx.length - 36))

ASSOC_RESPONSE = Struct("assoc_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt32("length"),
                        UBInt32("seq"),
                        Bytes("sta", 6))

ADD_LVAP = Struct("add_lvap", UBInt8("version"),
                  UBInt8("type"),
                  UBInt32("length"),
                  UBInt32("seq"),
                  UBInt16("group"),
                  BitStruct("flags", Padding(13),
                            Bit("set_mask"),
                            Bit("associated"),
                            Bit("authenticated")),
                  UBInt16("assoc_id"),
                  Bytes("hwaddr", 6),
                  UBInt8("channel"),
                  UBInt8("band"),
                  UBInt8("lvap_band"),
                  Bytes("sta", 6),
                  Bytes("encap", 6),
                  Bytes("net_bssid", 6),
                  Bytes("lvap_bssid", 6),
                  SSIDS)

DEL_LVAP = Struct("del_lvap", UBInt8("version"),
                  UBInt8("type"),
                  UBInt32("length"),
                  UBInt32("seq"),
                  Bytes("sta", 6))

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
                     UBInt8("lvap_band"),
                     Bytes("net_bssid", 6),
                     Bytes("lvap_bssid", 6),
                     SSIDS)

CAPS_R = Sequence("blocks",
                  Bytes("hwaddr", 6),
                  UBInt8("channel"),
                  UBInt8("band"))

CAPS_P = Sequence("ports", Bytes("hwaddr", 6),
                  UBInt16("port_id"),
                  Bytes("iface", 10))

CAPS = Struct("caps", UBInt8("version"),
              UBInt8("type"),
              UBInt32("length"),
              UBInt32("seq"),
              Bytes("wtp", 6),
              UBInt8("nb_resources_elements"),
              UBInt8("nb_ports_elements"),
              Array(lambda ctx: ctx.nb_resources_elements, CAPS_R),
              Array(lambda ctx: ctx.nb_ports_elements, CAPS_P))

SET_PORT = Struct("set_port", UBInt8("version"),
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

STATUS_PORT = Struct("status_port", UBInt8("version"),
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
                 Bytes("net_bssid", 6),
                 Bytes("ssid", lambda ctx: ctx.length - 24))

DEL_VAP = Struct("add_vap", UBInt8("version"),
                 UBInt8("type"),
                 UBInt32("length"),
                 UBInt32("seq"),
                 Bytes("net_bssid", 6))

STATUS_VAP = Struct("status_vap", UBInt8("version"),
                    UBInt8("type"),
                    UBInt32("length"),
                    UBInt32("seq"),
                    Bytes("wtp", 6),
                    Bytes("hwaddr", 6),
                    UBInt8("channel"),
                    UBInt8("band"),
                    Bytes("net_bssid", 6),
                    Bytes("ssid", lambda ctx: ctx.length - 30))

PT_TYPES = {PT_BYE: None,
            PT_REGISTER: None,
            PT_LVAP_JOIN: None,
            PT_LVAP_LEAVE: None,
            PT_HELLO: HELLO,
            PT_PROBE_REQUEST: PROBE_REQUEST,
            PT_PROBE_RESPONSE: PROBE_RESPONSE,
            PT_AUTH_REQUEST: AUTH_REQUEST,
            PT_AUTH_RESPONSE: AUTH_RESPONSE,
            PT_ASSOC_REQUEST: ASSOC_REQUEST,
            PT_ASSOC_RESPONSE: ASSOC_RESPONSE,
            PT_ADD_LVAP: ADD_LVAP,
            PT_DEL_LVAP: DEL_LVAP,
            PT_STATUS_LVAP: STATUS_LVAP,
            PT_CAPS: CAPS,
            PT_SET_PORT: SET_PORT,
            PT_STATUS_PORT: STATUS_PORT,
            PT_STATUS_VAP: STATUS_VAP}

PT_TYPES_HANDLERS = {PT_BYE: [],
                     PT_REGISTER: [],
                     PT_LVAP_JOIN: [],
                     PT_LVAP_LEAVE: [],
                     PT_HELLO: [],
                     PT_PROBE_REQUEST: [],
                     PT_PROBE_RESPONSE: [],
                     PT_AUTH_REQUEST: [],
                     PT_AUTH_RESPONSE: [],
                     PT_ASSOC_REQUEST: [],
                     PT_ASSOC_RESPONSE: [],
                     PT_ADD_LVAP: [],
                     PT_DEL_LVAP: [],
                     PT_STATUS_LVAP: [],
                     PT_CAPS: [],
                     PT_SET_PORT: [],
                     PT_STATUS_PORT: [],
                     PT_STATUS_VAP: []}
