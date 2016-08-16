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

PRT_VBSP_BYE = "bye"
PRT_VBSP_REGISTER = "register"
PRT_VBSP_HELLO = "mHello"
PRT_VBSP_CONFIGS = "mConfs"
PRT_VBSP_UE_CONFIG_REQUEST = "ue_conf_req"
PRT_VBSP_UE_CONFIG_RESPONSE = "ue_conf_repl"
PRT_VBSP_ENB_CONFIG_REQUEST = "enb_conf_req"
PRT_VBSP_ENB_CONFIG_RESPONSE = "enb_conf_repl"

PRT_TYPES = {PRT_VBSP_BYE: None,
             PRT_VBSP_REGISTER: None,
             PRT_VBSP_HELLO: "hello",
             PRT_VBSP_CONFIGS: "confs",
             PRT_VBSP_UE_CONFIG_REQUEST: None,
             PRT_VBSP_UE_CONFIG_RESPONSE: "ue_conf_repl",
             PRT_VBSP_ENB_CONFIG_REQUEST: None,
             PRT_VBSP_ENB_CONFIG_RESPONSE: "enb_conf_repl"}


PRT_TYPES_HANDLERS = {PRT_VBSP_BYE: [],
                      PRT_VBSP_REGISTER: [],
                      PRT_VBSP_HELLO: [],
                      PRT_VBSP_CONFIGS: [],
                      PRT_VBSP_UE_CONFIG_REQUEST: [],
                      PRT_VBSP_UE_CONFIG_RESPONSE: [],
                      PRT_VBSP_ENB_CONFIG_REQUEST: [],
                      PRT_VBSP_ENB_CONFIG_RESPONSE: []}
