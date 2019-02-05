#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

""" VBSP Server module. """

from construct import Sequence
from construct import Array
from construct import Struct
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import UBInt64
from construct import Bytes
from construct import Range
from construct import BitStruct
from construct import Bit
from construct import Padding
from construct import Probe
from construct import Enum
from construct import Rename
from construct import Byte
from construct import Switch
from construct import Pass
from construct import Field
from construct import OptionalGreedyRange
from construct import GreedyRange

PT_VERSION = 0x01

PT_BYE = "bye"
PT_REGISTER = "register"
PT_UE_JOIN = "ue_join"
PT_UE_LEAVE = "ue_leave"

EP_OPERATION_UNSPECIFIED = 0
EP_OPERATION_SUCCESS = 1
EP_OPERATION_FAIL = 2
EP_OPERATION_NOT_SUPPORTED = 3
EP_OPERATION_ADD = 4
EP_OPERATION_REM = 5
EP_OPERATION_SET = 6

EP_ACT_INVALID = 0
EP_ACT_HELLO = 1
EP_ACT_CAPS = 2
EP_ACT_UE_REPORT = 4
EP_ACT_HANDOVER = 7
EP_ACT_RAN_SETUP = 9
EP_ACT_RAN_MAC_SLICE = 10

E_TYPE_SINGLE = 0x01
E_TYPE_SCHED = 0x02
E_TYPE_TRIG = 0x03

OPTIONS = Struct("options",
                 UBInt16("type"),
                 UBInt16("length"),
                 Field("data", lambda ctx: ctx.length))

HEADER = Struct("header",
                UBInt8("type"),
                UBInt8("version"),
                Bytes("enbid", 8),
                UBInt16("cellid"),
                UBInt32("xid"),
                BitStruct("flags", Padding(15), Bit("dir")),
                UBInt32("seq"),
                UBInt16("length"))

E_SCHED = Struct("e_sched",
                 UBInt16("action"),
                 UBInt8("opcode"),
                 UBInt32("interval"))

E_SINGLE = Struct("e_single",
                  UBInt16("action"),
                  UBInt8("opcode"))

E_TRIG = Struct("e_trig",
                UBInt16("action"),
                UBInt8("opcode"))

HELLO = Struct("hello",
               UBInt32("padding"))

ENB_CAPS_REQUEST = Struct("caps_request",
                          UBInt8("type"),
                          UBInt8("version"),
                          Bytes("enbid", 8),
                          UBInt16("cellid"),
                          UBInt32("xid"),
                          BitStruct("flags", Padding(15), Bit("dir")),
                          UBInt32("seq"),
                          UBInt16("length"),
                          UBInt16("action"),
                          UBInt8("opcode"),
                          UBInt32("dummy"))

ENB_CAPS_RESPONSE = Struct("caps_response",
                           Rename("options",
                                  OptionalGreedyRange(OPTIONS)))

# Cell capabilities. This is a valid TLV for the ENB_CAPS_RESPONSE message.
CELL_CAPS = Struct("cell_caps",
                   UBInt16("pci"),
                   BitStruct("features", Padding(28),
                             Bit("handover"),
                             Bit("cell_measure"),
                             Bit("ue_measure"),
                             Bit("ue_report")),
                   UBInt16("dl_earfcn"),
                   UBInt8("dl_bandwidth"),
                   UBInt16("ul_earfcn"),
                   UBInt8("ul_bandwidth"),
                   UBInt16("max_ues"))

# RAN capabilities. This is a valid TLV for the ENB_CAPS_RESPONSE message.
RAN_CAPS = Struct("ran_caps",
                  UBInt16("pci"),
                  BitStruct("layer1", Padding(32)),
                  BitStruct("layer2", Padding(30),
                            Bit("prb_slicing"),
                            Bit("rbg_slicing")),
                  BitStruct("layer3", Padding(32)),
                  UBInt32("mac_sched"),
                  UBInt16("max_slices"))

RAN_MAC_SLICE_REQUEST = Struct("ran_mac_slice_request",
                               UBInt8("type"),
                               UBInt8("version"),
                               Bytes("enbid", 8),
                               UBInt16("cellid"),
                               UBInt32("xid"),
                               BitStruct("flags", Padding(15), Bit("dir")),
                               UBInt32("seq"),
                               UBInt16("length"),
                               UBInt16("action"),
                               UBInt8("opcode"),
                               Bytes("plmn_id", 4),
                               UBInt8("dscp"),
                               Bytes("padding", 3))

SET_RAN_MAC_SLICE_REQUEST = Struct("set_ran_mac_slice_request",
                                   UBInt8("type"),
                                   UBInt8("version"),
                                   Bytes("enbid", 8),
                                   UBInt16("cellid"),
                                   UBInt32("xid"),
                                   BitStruct("flags", Padding(15), Bit("dir")),
                                   UBInt32("seq"),
                                   UBInt16("length"),
                                   UBInt16("action"),
                                   UBInt8("opcode"),
                                   Bytes("plmn_id", 4),
                                   UBInt8("dscp"),
                                   Bytes("padding", 3),
                                   Rename("options",
                                          OptionalGreedyRange(OPTIONS)))

REM_RAN_MAC_SLICE_REQUEST = Struct("rem_ran_mac_slice_request",
                                   UBInt8("type"),
                                   UBInt8("version"),
                                   Bytes("enbid", 8),
                                   UBInt16("cellid"),
                                   UBInt32("xid"),
                                   BitStruct("flags", Padding(15), Bit("dir")),
                                   UBInt32("seq"),
                                   UBInt16("length"),
                                   UBInt16("action"),
                                   UBInt8("opcode"),
                                   Bytes("plmn_id", 4),
                                   UBInt8("dscp"),
                                   Bytes("padding", 3))

RAN_MAC_SLICE_RESPONSE = Struct("ran_mac_slice_response",
                                Bytes("plmn_id", 4),
                                UBInt8("dscp"),
                                Bytes("padding", 3),
                                Rename("options",
                                       OptionalGreedyRange(OPTIONS)))

UE_REPORT_REQUEST = Struct("ue_report_request",
                           UBInt8("type"),
                           UBInt8("version"),
                           Bytes("enbid", 8),
                           UBInt16("cellid"),
                           UBInt32("xid"),
                           BitStruct("flags", Padding(15), Bit("dir")),
                           UBInt32("seq"),
                           UBInt16("length"),
                           UBInt16("action"),
                           UBInt8("opcode"),
                           UBInt32("dummy"))

UE_REPORT_RESPONSE = Struct("ue_report_response",
                            Rename("options",
                                   OptionalGreedyRange(OPTIONS)))

# UE_REPORT_IDENTITY. This is a valid TLV for the UE_REPORT_RESPONSE message.
UE_REPORT_IDENTITY = Struct("ue_report_identity",
                            UBInt16("rnti"),
                            Bytes("plmn_id", 4),
                            UBInt64("imsi"),
                            UBInt32("tmsi"),
                            UBInt8("state"))

UE_HO_REQUEST = Struct("ue_ho_request",
                       UBInt8("type"),
                       UBInt8("version"),
                       Bytes("enbid", 8),
                       UBInt16("cellid"),
                       UBInt32("xid"),
                       BitStruct("flags", Padding(15), Bit("dir")),
                       UBInt32("seq"),
                       UBInt16("length"),
                       UBInt16("action"),
                       UBInt8("opcode"),
                       UBInt16("rnti"),
                       Bytes("target_enbid", 8),
                       UBInt16("target_pci"),
                       UBInt8("cause"))

UE_HO_RESPONSE = Struct("ue_ho_response",
                        Bytes("origin_enbid", 8),
                        UBInt16("origin_pci"),
                        UBInt16("origin_rnti"),
                        UBInt16("target_rnti"))

# RBGs to allocate to a slice. This is a valid TLV for the
# RAN_MAC_SLICE_REQUEST message.
RAN_MAC_SLICE_RBGS = Struct("ran_mac_slice_rbgs", UBInt16("rbgs"))

# Scheduler to be used for a a slice. This is a valid TLV for the
# RAN_MAC_SLICE_REQUEST message.
RAN_MAC_SLICE_SCHED_ID = Struct("ran_mac_slice_sched_id", UBInt32("sched_id"))

# RNTIs to be mappeted to a a slice. This is a valid TLV for the
# RAN_MAC_SLICE_REQUEST message.
RAN_MAC_SLICE_RNTI_LIST = Struct("ran_mac_slice_rntis",
                                 OptionalGreedyRange(UBInt16("rntis")))

# TLV dictionaries

EP_CELL_CAPS = 0x0100
EP_RAN_CAPS = 0x0503

ENB_CAPS_TYPES = {
    EP_CELL_CAPS: CELL_CAPS,
    EP_RAN_CAPS: RAN_CAPS
}

EP_RAN_MAC_SLICE_SCHED_ID = 0x0502
EP_RAN_MAC_SLICE_RBGS = 0x0501
EP_RAN_MAC_SLICE_RNTI_LIST = 0x0001

RAN_MAC_SLICE_TYPES = {
    EP_RAN_MAC_SLICE_RBGS: RAN_MAC_SLICE_RBGS,
    EP_RAN_MAC_SLICE_SCHED_ID: RAN_MAC_SLICE_SCHED_ID,
    EP_RAN_MAC_SLICE_RNTI_LIST: RAN_MAC_SLICE_RNTI_LIST
}

EP_UE_REPORT_IDENTITY = 0x0700
EP_UE_REPORT_STATE = 0x0701

UE_REPORT_TYPES = {
    EP_UE_REPORT_IDENTITY: UE_REPORT_IDENTITY
}

PT_TYPES = {PT_BYE: None,
            PT_REGISTER: None,
            PT_UE_JOIN: None,
            PT_UE_LEAVE: None,
            EP_ACT_HELLO: HELLO,
            EP_ACT_CAPS: ENB_CAPS_RESPONSE,
            EP_ACT_RAN_MAC_SLICE: RAN_MAC_SLICE_RESPONSE,
            EP_ACT_UE_REPORT: UE_REPORT_RESPONSE,
            EP_ACT_HANDOVER: UE_HO_RESPONSE}

PT_TYPES_HANDLERS = {PT_BYE: [],
                     PT_REGISTER: [],
                     PT_UE_JOIN: [],
                     PT_UE_LEAVE: [],
                     EP_ACT_HELLO: [],
                     EP_ACT_CAPS: [],
                     EP_ACT_RAN_SETUP: [],
                     EP_ACT_RAN_MAC_SLICE: [],
                     EP_ACT_UE_REPORT: [],
                     EP_ACT_HANDOVER: []}
