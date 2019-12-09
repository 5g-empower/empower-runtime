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

"""VBSP RAN Manager."""

from construct import Struct, Int8ub, Int16ub, Int32ub, Flag, Bytes, Bit, \
    BitStruct, Padding

PT_VERSION = 0x00

PT_DEVICE_DOWN = "device_down"
PT_DEVICE_UP = "device_up"
PT_CLIENT_JOIN = "client_join"
PT_CLIENT_LEAVE = "client_leave"

# action, type, opcode
PT_HELLO_REQUEST = (0x01, 0, 3)
PT_HELLO_RESPONSE = (0x01, 1, 3)

HEADER = Struct(
    "version" / Int8ub,
    "flags" / BitStruct(
        "padding" / Padding(7),
        "request_response" / Flag
    ),
    "reserved1" / Int16ub,
    "length" / Int32ub,
    "action" / Bytes(14),
    "crud_succfail" / Bytes(2),
    "pci" / Int16ub,
    "device" / Bytes(8),
    "seq" / Int32ub,
    "xid" / Int32ub,
)
HEADER.name = "header"

HELLO_REQUEST = Struct(
    "version" / Int8ub,
    "flags" / BitStruct(
        "padding" / Padding(7),
        "type" / Flag
    ),
    "reserved1" / Int16ub,
    "length" / Int32ub,
    "action" / Bytes(14),
    "opcode" / Bytes(2),
    "reserved2" / Int16ub,
    "device" / Bytes(8),
    "seq" / Int32ub,
    "xid" / Int32ub,
)
HELLO_REQUEST.name = "hello_request"

HELLO_RESPONSE = Struct(
    "version" / Int8ub,
    "flags" / BitStruct(
        "padding" / Padding(7),
        "ack" / Flag
    ),
    "reserved1" / Int16ub,
    "length" / Int32ub,
    "action" / Bytes(14),
    "opcode" / Bytes(2),
    "reserved2" / Int16ub,
    "device" / Bytes(8),
    "seq" / Int32ub,
    "xid" / Int32ub,
)
HELLO_RESPONSE.name = "hello_response"

PT_TYPES = {

    PT_DEVICE_DOWN: None,
    PT_DEVICE_UP: None,
    PT_CLIENT_JOIN: None,
    PT_CLIENT_LEAVE: None,

    PT_HELLO_REQUEST: HELLO_REQUEST,
    PT_HELLO_RESPONSE: HELLO_RESPONSE,

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
