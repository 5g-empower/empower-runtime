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

""" VBSP Server module. """

from construct import Struct
from construct import UBInt32
from enum import IntEnum, Enum

PROGRAN_VERSION = 0
NUM_MAX_ENB = 2
NUM_MAX_UE = 2048
DEFAULT_PORT = 2210


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
             PRT_UE_STATE_CHANGE: None,
             PRT_UE_CONFIG_REQUEST: None,
             PRT_UE_CONFIG_RESPONSE: None,
             PRT_ENB_CONFIG_REQUEST: None,
             PRT_ENB_CONFIG_RESPONSE: None,
             PRT_LC_CONFIG_REQUEST: None,
             PRT_LC_CONFIG_RESPONSE: None,
             PRT_DL_MAC_CONFIG_MESSAGE: None,
             PRT_CONTROL_DELEGATION_MESSAGE: None}


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
                      PRT_CONTROL_DELEGATION_MESSAGE: []}
