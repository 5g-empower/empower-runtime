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
    BitStruct, Padding, BitsInteger, Array, GreedyRange, Byte, this, Int64ub

PT_VERSION = 0x02

MSG_TYPE_REQUEST = 0
MSG_TYPE_RESPONSE = 1

RESULT_SUCCESS = 0
RESULT_FAIL = 1

OP_UNDEFINED = 0
OP_UPDATE = 1
OP_CREATE = 2
OP_DELETE = 3
OP_RETRIEVE = 4

PT_DEVICE_DOWN = "device_down"
PT_DEVICE_UP = "device_up"
PT_CLIENT_JOIN = "client_join"
PT_CLIENT_LEAVE = "client_leave"

PT_HELLO_SERVICE = 0x00
PT_CAPABILITIES_SERVICE = 0x01
PT_UE_REPORTS_SERVICE = 0x02

TLVS = Struct(
    "type" / Int16ub,
    "length" / Int16ub,
    "value" / Bytes(this.length - 4),
)

HEADER = Struct(
    "version" / Int8ub,
    "flags" / BitStruct(
        "msg_type" / Flag,
        "padding" / Padding(7)
    ),
    "tsrc" / BitStruct(
        "crud_result" / BitsInteger(2),
        "action" / BitsInteger(14),
    ),
    "length" / Int32ub,
    "padding" / Bytes(2),
    "device" / Bytes(6),
    "seq" / Int32ub,
    "xid" / Int32ub,
)

PACKET = Struct(
    "version" / Int8ub,
    "flags" / BitStruct(
        "msg_type" / Flag,
        "padding" / Padding(7)
    ),
    "tsrc" / BitStruct(
        "crud_result" / BitsInteger(2),
        "action" / BitsInteger(14),
    ),
    "length" / Int32ub,
    "padding" / Bytes(2),
    "device" / Bytes(6),
    "seq" / Int32ub,
    "xid" / Int32ub,
    "tlvs" / GreedyRange(TLVS)
)

# TLV dicts

PT_HELLO_SERVICE_PERIOD = 0x04
PT_CAPABILITIES_SERVICE_CELL = 0x06
PT_UE_REPORTS_SERVICE_IDENTITY = 0x07

HELLO_SERVICE_PERIOD = Struct(
    "period" / Int32ub
)
HELLO_SERVICE_PERIOD.name = "hello_service_period"

CAPABILITIES_SERVICE_CELL = Struct(
    "pci" / Int16ub,
    "dl_earfcn" / Int32ub,
    "ul_earfcn" / Int32ub,
    "n_prbs" / Int8ub
)
CAPABILITIES_SERVICE_CELL.name = "capabilities_service_cell"

UE_REPORTS_SERVICE_IDENTITY = Struct(
    "imsi" / Int64ub,
    "tmsi" / Int32ub,
    "rnti" / Int16ub,
    "status" / Int8ub,
    "pci" / Int16ub,
)
UE_REPORTS_SERVICE_IDENTITY.name = "ue_reports_service_identity"


TLVS = {
    PT_HELLO_SERVICE_PERIOD: HELLO_SERVICE_PERIOD,
    PT_CAPABILITIES_SERVICE_CELL: CAPABILITIES_SERVICE_CELL,
    PT_UE_REPORTS_SERVICE_IDENTITY: UE_REPORTS_SERVICE_IDENTITY,
}

# Packet types

PT_TYPES = {

    PT_DEVICE_DOWN: None,
    PT_DEVICE_UP: None,
    PT_CLIENT_JOIN: None,
    PT_CLIENT_LEAVE: None,

    PT_HELLO_SERVICE: (PACKET, "hello_service"),
    PT_CAPABILITIES_SERVICE: (PACKET, "capabilities_service"),
    PT_UE_REPORTS_SERVICE: (PACKET, "ue_reports_service"),

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


def register_callbacks(app, callback_str='handle_'):
    """Register callbacks."""

    for pt_type in PT_TYPES_HANDLERS:

        if not PT_TYPES[pt_type]:
            handler_name = callback_str + pt_type
        else:
            handler_name = callback_str + PT_TYPES[pt_type][1]

        if hasattr(app, handler_name):
            handler = getattr(app, handler_name)
            PT_TYPES_HANDLERS[pt_type].append(handler)


def unregister_callbacks(app, callback_str='handle_'):
    """Unregister callbacks."""

    for pt_type in PT_TYPES_HANDLERS:

        if not PT_TYPES[pt_type]:
            handler_name = callback_str + pt_type
        else:
            handler_name = callback_str + PT_TYPES[pt_type][1]

        if hasattr(app, handler_name):
            handler = getattr(app, handler_name)
            PT_TYPES_HANDLERS[pt_type].remove(handler)


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


def decode_msg(msg_type, crud_result):
    """Return the tuple (msg_type, crud_result)."""

    if int(msg_type) == MSG_TYPE_REQUEST:

        msg_type_str = "request"

        if crud_result == OP_UNDEFINED:
            crud_result_str = "undefined"
        elif crud_result == OP_CREATE:
            crud_result_str = "create"
        elif crud_result == OP_UPDATE:
            crud_result_str = "update"
        elif crud_result == OP_DELETE:
            crud_result_str = "delete"
        elif crud_result == OP_RETRIEVE:
            crud_result_str = "retrieve"
        else:
            crud_result_str = "unknown"

        return (msg_type_str, crud_result_str)

    msg_type_str = "response"

    if crud_result == RESULT_SUCCESS:
        crud_result_str = "success"
    elif crud_result == RESULT_FAIL:
        crud_result_str = "fail"
    else:
        crud_result_str = "unknown"

    return (msg_type_str, crud_result_str)
