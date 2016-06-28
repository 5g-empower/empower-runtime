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

""" VBSP Server module. """

from construct import Struct
from construct import UBInt32
from enum import IntEnum, Enum

PROGRAN_VERSION = 0
NUM_MAX_ENB = 2
NUM_MAX_UE = 2048
DEFAULT_CONTROLLER_AGENT_IPv4_ADDRESS = "127.0.0.1"
DEFAULT_PORT = 2210


MAC_STATS_TYPE = {}

MAC_STATS_REPORT_FREQ = {}

MAC_CELL_STATS_TYPES = {}

MAC_UE_STATS_TYPES = {}

TIMER_IDS = []

HELLO_MSG_MODULE_ID = 4294967294
MISC_MSG_MODULE_ID = 4294967295

RESERVED_MODULE_IDS = [HELLO_MSG_MODULE_ID, MISC_MSG_MODULE_ID]
MAX_MODULE_ID = 4294967295 # Max value of uint32

MAX_NUM_CCs = 1


class AgentIDT(IntEnum):

    CTRL_AGENT_DEFAULT = 0

    CTRL_AGENT_PHY = 1
    CTRL_AGENT_MAC = 2
    CTRL_AGENT_RLC = 3
    CTRL_AGENT_PDCP = 4
    CTRL_AGENT_RRC = 5
    CTRL_AGENT_S1AP = 6
    CTRL_AGENT_GTP = 7
    CTRL_AGENT_X2AP = 8

    CTRL_AGENT_MAX = 9


class AgentActionT(Enum):

    # no action
    CTRL_AGENT_ACTION_NONE = 0x0

    # send action
    CTRL_AGENT_ACTION_SEND = 0x1

    # apply action
    CTRL_AGENT_ACTION_APPLY = 0x2

    # clear action
    CTRL_AGENT_ACTION_CLEAR = 0x4

    # write action
    CTRL_AGENT_ACTION_WRITE = 0x8

    # filter action
    CTRL_AGENT_ACTION_FILTER = 0x10

    # preprocess action
    CTRL_AGENT_ACTION_PREPROCESS = 0x20

    # meter action
    CTRL_AGENT_ACTION_METER = 0x40

    # Max number of states available
    CTRL_AGENT_ACTION_MAX = 0x7f


MESSAGE_SIZE = Struct("message_size", UBInt32("length"))


PT_VERSION = 0x00

PRT_VBSP_BYE = "agent_bye"
PRT_VBSP_REGISTER = "agent_register"
PRT_VBSP_UP = "agent_up"
PRT_VBSP_DOWN = "agent_down"
PRT_VBSP_AUTH_REQUEST = "agent_auth_req"
PRT_VBSP_AUTH_RESPONSE = "agent_auth_reply"
PRT_VBSP_HELLO = "hello_msg"
PRT_VBSP_ECHO_REQUEST = "echo_request_msg"
PRT_VBSP_ECHO_RESPONSE = "echo_reply_msg"
PRT_MAC_STATS_REQUEST = "stats_request_msg"
PRT_MAC_STATS_RESPONSE = "stats_reply_msg"
PRT_SF_TRIGGER_MESSAGE = "sf_trigger_msg"
PRT_UL_SR_INFO_MESSAGE = "ul_sr_info_msg"
PRT_UE_CONFIG_REQUEST = "ue_config_request_msg"
PRT_UE_CONFIG_RESPONSE = "ue_config_reply_msg"
PRT_ENB_CONFIG_REQUEST = "enb_config_request_msg"
PRT_ENB_CONFIG_RESPONSE = "enb_config_reply_msg"
PRT_LC_CONFIG_REQUEST = "lc_config_request_msg"
PRT_LC_CONFIG_RESPONSE = "lc_config_reply_msg"
PRT_DL_MAC_CONFIG_MESSAGE = "dl_mac_config_msg"
PRT_CONTROL_DELEGATION_MESSAGE = "control_delegation_msg"
PRT_UE_STATE_CHANGE = "ue_state_change_msg"
PRT_UE_RRC_MEASUREMENTS_RESPONSE = "ue_rrc_measurements_reply_msg"


PRT_TYPES = {PRT_VBSP_BYE: None,
             PRT_VBSP_REGISTER: None,
             PRT_VBSP_UP: None,
             PRT_VBSP_DOWN: None,
             PRT_VBSP_AUTH_REQUEST: None,
             PRT_VBSP_AUTH_RESPONSE: None,
             PRT_VBSP_HELLO: "hello",
             PRT_VBSP_ECHO_REQUEST: "echo_request",
             PRT_VBSP_ECHO_RESPONSE: "echo_response",
             PRT_MAC_STATS_REQUEST: "mac_stats_request",
             PRT_MAC_STATS_RESPONSE: "mac_stats_response",
             PRT_SF_TRIGGER_MESSAGE: None,
             PRT_UL_SR_INFO_MESSAGE: None,
             PRT_UE_STATE_CHANGE: "ue_state_change",
             PRT_UE_CONFIG_REQUEST: None,
             PRT_UE_CONFIG_RESPONSE: None,
             PRT_ENB_CONFIG_REQUEST: None,
             PRT_ENB_CONFIG_RESPONSE: "enb_config_reply",
             PRT_LC_CONFIG_REQUEST: None,
             PRT_LC_CONFIG_RESPONSE: None,
             PRT_DL_MAC_CONFIG_MESSAGE: None,
             PRT_CONTROL_DELEGATION_MESSAGE: None,
             PRT_UE_RRC_MEASUREMENTS_RESPONSE: "ue_rrc_measurements_reply"}


PRT_TYPES_HANDLERS = {PRT_VBSP_BYE: [],
                      PRT_VBSP_REGISTER: [],
                      PRT_VBSP_UP: [],
                      PRT_VBSP_DOWN: [],
                      PRT_VBSP_AUTH_REQUEST: [],
                      PRT_VBSP_AUTH_RESPONSE: [],
                      PRT_VBSP_HELLO: [],
                      PRT_VBSP_ECHO_REQUEST: [],
                      PRT_VBSP_ECHO_RESPONSE: [],
                      PRT_MAC_STATS_REQUEST: [],
                      PRT_MAC_STATS_RESPONSE: [],
                      PRT_SF_TRIGGER_MESSAGE: [],
                      PRT_UL_SR_INFO_MESSAGE: [],
                      PRT_UE_STATE_CHANGE: [],
                      PRT_UE_CONFIG_REQUEST: [],
                      PRT_UE_CONFIG_RESPONSE: [],
                      PRT_ENB_CONFIG_REQUEST: [],
                      PRT_ENB_CONFIG_RESPONSE: [],
                      PRT_LC_CONFIG_REQUEST: [],
                      PRT_LC_CONFIG_RESPONSE: [],
                      PRT_DL_MAC_CONFIG_MESSAGE: [],
                      PRT_CONTROL_DELEGATION_MESSAGE: [],
                      PRT_UE_RRC_MEASUREMENTS_RESPONSE: []}
