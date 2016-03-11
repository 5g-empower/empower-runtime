#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
PT_REGISTER = 0xFF
PT_LVAP_JOIN = 0x01
PT_LVAP_LEAVE = 0x02
PT_HELLO = 0x03
PT_PROBE_REQUEST = 0x04
PT_PROBE_RESPONSE = 0x05
PT_AUTH_REQUEST = 0x06
PT_AUTH_RESPONSE = 0x07
PT_ASSOC_REQUEST = 0x08
PT_ASSOC_RESPONSE = 0x09
PT_ADD_LVAP = 0x10
PT_DEL_LVAP = 0x11
PT_STATUS_LVAP = 0x12
PT_SET_PORT = 0x13
PT_STATUS_PORT = 0x14
PT_CAPS_REQUEST = 0x15
PT_CAPS_RESPONSE = 0x16

HEADER = Struct("header", UBInt8("version"), UBInt8("type"), UBInt16("length"))

SSIDS = Range(1, 10, Struct("ssids", UBInt8("length"),
                            Bytes("ssid", lambda ctx: ctx.length)))

HELLO = Struct("hello", UBInt8("version"),
               UBInt8("type"),
               UBInt16("length"),
               UBInt32("seq"),
               UBInt32("period"),
               Bytes("wtp", 6),
               UBInt32("uplink_bytes"),
               UBInt32("downlink_bytes"))

PROBE_REQUEST = Struct("probe_request", UBInt8("version"),
                       UBInt8("type"),
                       UBInt16("length"),
                       UBInt32("seq"),
                       Bytes("wtp", 6),
                       Bytes("sta", 6),
                       UBInt8("channel"),
                       UBInt8("band"),
                       Bytes("ssid", lambda ctx: ctx.length - 22))

PROBE_RESPONSE = Struct("probe_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt16("length"),
                        UBInt32("seq"),
                        Bytes("sta", 6))

AUTH_REQUEST = Struct("auth_request", UBInt8("version"),
                      UBInt8("type"),
                      UBInt16("length"),
                      UBInt32("seq"),
                      Bytes("wtp", 6),
                      Bytes("sta", 6))

AUTH_RESPONSE = Struct("auth_response", UBInt8("version"),
                       UBInt8("type"),
                       UBInt16("length"),
                       UBInt32("seq"),
                       Bytes("sta", 6))

ASSOC_REQUEST = \
    Struct("assoc_request", UBInt8("version"),
           UBInt8("type"),
           UBInt16("length"),
           UBInt32("seq"),
           Bytes("wtp", 6),
           Bytes("sta", 6),
           Bytes("ssid", lambda ctx: ctx.length - 20))

ASSOC_RESPONSE = Struct("assoc_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt16("length"),
                        UBInt32("seq"),
                        Bytes("sta", 6))

ADD_LVAP = Struct("add_lvap", UBInt8("version"),
                  UBInt8("type"),
                  UBInt16("length"),
                  UBInt32("seq"),
                  BitStruct("flags", Padding(13),
                            Bit("set_mask"),
                            Bit("associated"),
                            Bit("authenticated")),
                  UBInt16("assoc_id"),
                  UBInt8("channel"),
                  UBInt8("band"),
                  Bytes("sta", 6),
                  Bytes("encap", 6),
                  Bytes("bssid", 6),
                  SSIDS)

DEL_LVAP = Struct("del_lvap", UBInt8("version"),
                  UBInt8("type"),
                  UBInt16("length"),
                  UBInt32("seq"),
                  Bytes("sta", 6))

STATUS_LVAP = Struct("status_lvap", UBInt8("version"),
                     UBInt8("type"),
                     UBInt16("length"),
                     UBInt32("seq"),
                     BitStruct("flags", Padding(13),
                               Bit("set_mask"),
                               Bit("associated"),
                               Bit("authenticated")),
                     UBInt16("assoc_id"),
                     Bytes("wtp", 6),
                     Bytes("sta", 6),
                     Bytes("encap", 6),
                     UBInt8("channel"),
                     UBInt8("band"),
                     Bytes("bssid", 6),
                     SSIDS)

CAPS_REQUEST = Struct("caps_request", UBInt8("version"),
                      UBInt8("type"),
                      UBInt16("length"),
                      UBInt32("seq"))

CAPS_R = Sequence("blocks", UBInt8("channel"),
                  UBInt8("band"),
                  BitStruct("flags", Padding(15), Bit("blacklisted")))

CAPS_P = Sequence("ports", Bytes("hwaddr", 6),
                  UBInt16("port_id"),
                  Bytes("iface", 10))

CAPS_RESPONSE = Struct("caps_response", UBInt8("version"),
                       UBInt8("type"),
                       UBInt16("length"),
                       UBInt32("seq"),
                       Bytes("wtp", 6),
                       UBInt8("nb_resources_elements"),
                       UBInt8("nb_ports_elements"),
                       Array(lambda ctx: ctx.nb_resources_elements, CAPS_R),
                       Array(lambda ctx: ctx.nb_ports_elements, CAPS_P))

SET_PORT = Struct("set_port", UBInt8("version"),
                  UBInt8("type"),
                  UBInt16("length"),
                  UBInt32("seq"),
                  BitStruct("flags", Padding(15),
                            Bit("no_ack")),
                  Bytes("sta", 6),
                  UBInt8("tx_power"),
                  UBInt16("rts_cts"),
                  UBInt8("nb_mcses"),
                  Array(lambda ctx: ctx.nb_mcses, UBInt8("mcs")))

STATUS_PORT = Struct("status_port", UBInt8("version"),
                     UBInt8("type"),
                     UBInt16("length"),
                     UBInt32("seq"),
                     BitStruct("flags", Padding(15),
                               Bit("no_ack")),
                     Bytes("wtp", 6),
                     Bytes("sta", 6),
                     UBInt8("channel"),
                     UBInt8("band"),
                     UBInt8("tx_power"),
                     UBInt16("rts_cts"),
                     UBInt8("nb_mcses"),
                     Array(lambda ctx: ctx.nb_mcses, UBInt8("mcs")))

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
            PT_CAPS_REQUEST: CAPS_REQUEST,
            PT_CAPS_RESPONSE: CAPS_RESPONSE,
            PT_SET_PORT: SET_PORT,
            PT_STATUS_PORT: STATUS_PORT}

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
                     PT_CAPS_REQUEST: [],
                     PT_CAPS_RESPONSE: [],
                     PT_SET_PORT: [],
                     PT_STATUS_PORT: []}
