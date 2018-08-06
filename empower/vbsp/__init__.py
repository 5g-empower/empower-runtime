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

EP_ACT_INVALID = 0
EP_ACT_HELLO = 1
EP_ACT_CAPS = 2
EP_ACT_UE_REPORT = 4
EP_ACT_UE_MEASURE = 5
EP_ACT_HANDOVER = 7
EP_ACT_RAN_SETUP = 9

EP_CAPS_CELL = 0x0100
EP_CAPS_RAN_MAC_SCHED = 0x0500

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

CAPS_REQUEST = Struct("caps_request",
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

CAPS_RESPONSE = Struct("caps_response",
                       BitStruct("flags", Padding(29),
                                 Bit("handover"),
                                 Bit("ue_measure"),
                                 Bit("ue_report")),
                       Rename("options", OptionalGreedyRange(OPTIONS)))

RAN_SETUP_REQUEST = Struct("ran_setup_request",
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

RAN_SETUP_RESPONSE = Struct("ran_setup_response",
                       BitStruct("layer1", Padding(32)),
                       BitStruct("layer2", Padding(31),
                                 Bit("prb_slicing")),
                       BitStruct("layer3", Padding(32)),
                       Rename("options", OptionalGreedyRange(OPTIONS)))

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

UE_R = Struct("ues",
              UBInt16("pci"),
              Bytes("plmn_id", 4),
              UBInt16("rnti"),
              UBInt64("imsi"))

UE_REPORT_RESPONSE = Struct("ue_report_response",
                            UBInt32("nof_ues"),
                            Array(lambda ctx: ctx.nof_ues, UE_R))

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

CAPS_CELL = Struct("caps_tlv_cell",
                   UBInt16("pci"),
                   BitStruct("cap", Padding(29),
                    Bit("ran_slicing"),
                    Bit("mac_report"),
                    Bit("phy_report")),
                   UBInt16("dl_earfcn"),
                   UBInt8("dl_prbs"),
                   UBInt16("ul_earfcn"),
                   UBInt8("ul_prbs"))

CAPS_RAN_MAC_SCHED = Struct("caps_ran_mac_sched",
                   UBInt32("sched_id"))

CAPS_TYPES = {
    EP_CAPS_CELL: CAPS_CELL,
    EP_CAPS_RAN_MAC_SCHED: CAPS_RAN_MAC_SCHED
}

PT_TYPES = {PT_BYE: None,
            PT_REGISTER: None,
            PT_UE_JOIN: None,
            PT_UE_LEAVE: None,
            EP_ACT_HELLO: HELLO,
            EP_ACT_CAPS: CAPS_RESPONSE,
            EP_ACT_RAN_SETUP: RAN_SETUP_RESPONSE,
            EP_ACT_UE_REPORT: UE_REPORT_RESPONSE,
            EP_ACT_HANDOVER: UE_HO_RESPONSE}

PT_TYPES_HANDLERS = {PT_BYE: [],
                     PT_REGISTER: [],
                     PT_UE_JOIN: [],
                     PT_UE_LEAVE: [],
                     EP_ACT_HELLO: [],
                     EP_ACT_CAPS: [],
                     EP_ACT_RAN_SETUP: [],
                     EP_ACT_UE_REPORT: [],
                     EP_ACT_HANDOVER: []}
