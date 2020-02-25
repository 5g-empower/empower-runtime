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

"""VBSP protocols."""

from construct import Struct, Int8ub, Int16ub, Int32ub, Bytes, Array, \
    BitStruct, Padding, Flag, GreedyRange, BitsInteger


PT_VERSION = 0x00

PT_DEVICE_DOWN = "device_down"
PT_DEVICE_UP = "device_up"
PT_CLIENT_JOIN = "client_join"
PT_CLIENT_LEAVE = "client_leave"

PT_HELLO_REQUEST = 0x01
PT_HELLO_RESPONSE = 0x02

PT_CAPS_REQUEST = 0x03
PT_CAPS_RESPONSE = 0x04

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

# Cell capabilities. This is a valid TLV for the CAPS_RESPONSE message.
CAPS_CELLS = Struct(
    "pci" / Int16ub,
    "flags" / BitStruct(
        "padding" / Padding(28),
        "handover" / Flag,
        "cell_measure" / Flag,
        "ue_measure" / Flag,
        "ue_report" / Flag,
    ),
    "dl_earfcn" / Int16ub,
    "dl_bandwidth" / Int8ub,
    "ul_earfcn" / Int16ub,
    "max_ues" / Int8ub,
)

CAPS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "options" / GreedyRange(
        Struct(
            "type" / Int16ub,
            "length" / Int16ub,
            "data" / Bytes(lambda ctx: ctx.length)
        )
    )
)
CAPS_RESPONSE.name = "caps_response"

PT_TYPES = {

    PT_DEVICE_DOWN: None,
    PT_DEVICE_UP: None,
    PT_CLIENT_JOIN: None,
    PT_CLIENT_LEAVE: None,

    PT_HELLO_REQUEST: HELLO_REQUEST,
    PT_HELLO_RESPONSE: HELLO_RESPONSE,

    PT_CAPS_RESPONSE: CAPS_RESPONSE,
    PT_CAPS_REQUEST: CAPS_REQUEST,

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
