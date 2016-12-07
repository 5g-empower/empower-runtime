#!/usr/bin/env python3
#
# Copyright (c) 2016 Supreeth Herle
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

"""VBSP Server module."""

EMAGE_VERSION = 1

MAX_NUM_CCS = 1

PRT_UE_JOIN = "join"
PRT_UE_LEAVE = "leave"
PRT_VBSP_BYE = "bye"
PRT_VBSP_REGISTER = "register"
PRT_VBSP_TRIGGER_EVENT = "te"
PRT_VBSP_AGENT_SCHEDULED_EVENT = "sche"
PRT_VBSP_SINGLE_EVENT = "se"
PRT_VBSP_HELLO = "mHello"
PRT_VBSP_UES_ID = "mUEs_id"
PRT_VBSP_RRC_MEAS_CONF = "mUE_rrc_meas_conf"
PRT_VBSP_STATS = "mStats"

PRT_TYPES = {PRT_VBSP_BYE: None,
             PRT_VBSP_REGISTER: None,
             PRT_UE_JOIN: None,
             PRT_UE_LEAVE: None,
             PRT_VBSP_HELLO: "hello",
             PRT_VBSP_UES_ID: "UEs_id_repl",
             PRT_VBSP_RRC_MEAS_CONF: None,
             PRT_VBSP_STATS: None}


PRT_TYPES_HANDLERS = {PRT_VBSP_BYE: [],
                      PRT_VBSP_REGISTER: [],
                      PRT_UE_JOIN: [],
                      PRT_UE_LEAVE: [],
                      PRT_VBSP_HELLO: [],
                      PRT_VBSP_UES_ID: []}
