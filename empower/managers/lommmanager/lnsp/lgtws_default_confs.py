#!/usr/bin/env python3
#
# Copyright (c) 2019, CREATE-NET FBK, Trento, Italy
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

# From https://github.com/lorabasics/basicstation/blob/master/pysys/tcutils.py w/ small changes
LGTW_CONFIG_EU863_6CH = {
    'nocca':False,   # channel assessment
    'nodc':True,     # duty-cycle
    'nodwell':False, # dwell-time
    'DRs': [[12, 125, 0],
        [11, 125, 0],
        [10, 125, 0],
        [9, 125, 0],
        [8, 125, 0],
        [7, 125, 0],
        [6, 250, 0],
        [0, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0]],
    'JoinEui': None,
    'NetID': None,
    'bcning': None,
    'config': {},
    'nodc': True,
    'freq_range': [863000000, 870000000],
    'hwspec': 'sx1301/1',
    'max_eirp': 16.0,
    'msgtype': 'router_config',
    'protocol': 1,
    'region': 'EU863',
    'regionid': 1002,
    # 'sx1301_conf': [{'chan_FSK': {'enable': False},
                 # 'chan_Lora_std': {'enable': False},
                 # 'chan_multiSF_0': {'enable': True, 'if': -375000, 'radio': 0},
                 # 'chan_multiSF_1': {'enable': True, 'if': -175000, 'radio': 0},
                 # 'chan_multiSF_2': {'enable': True, 'if': 25000, 'radio': 0},
                 # 'chan_multiSF_3': {'enable': True, 'if': 375000, 'radio': 0},
                 # 'chan_multiSF_4': {'enable': True, 'if': -237500, 'radio': 1},
                 # 'chan_multiSF_5': {'enable': True, 'if': 237500, 'radio': 1},
                 # 'chan_multiSF_6': {'enable': False},
                 # 'chan_multiSF_7': {'enable': False},
                 # 'radio_0': {'enable': True, 'freq': 868475000},
                 # 'radio_1': {'enable': True, 'freq': 869287500}}],
    # SEMTECH's live configuration
    'sx1301_conf': [{'chan_FSK': {'enable': False},
                 'chan_Lora_std': {'enable': False},
                 'chan_multiSF_0': {'enable': True, 'if': -200000, 'radio': 0},
                 'chan_multiSF_1': {'enable': True, 'if': 0, 'radio': 0},
                 'chan_multiSF_2': {'enable': True, 'if': 200000, 'radio': 0},
                 'chan_multiSF_3': {'enable': False},
                 'chan_multiSF_4': {'enable': False},
                 'chan_multiSF_5': {'enable': False},
                 'chan_multiSF_6': {'enable': False},
                 'chan_multiSF_7': {'enable': False},
                 'radio_0': {'enable': True,  'freq': 868300000},    # live configuration
                 'radio_1': {'enable': False, 'freq': 0}}],  # live configuration
    'upchannels': [[868100000, 0, 5],
               [868300000, 0, 5],
               [868500000, 0, 5],
               [868850000, 0, 5],
               [869050000, 0, 5],
               [869525000, 0, 5]]
}

LGTW_CONFIG_GENERIC = {
            "NetID":[0],
            "JoinEui":[[0,0]],
            "region":"EU863",
            "hwspec":"sx1301/1",
            "freq_range":[863,670],
            "DRs":[[12, 125, 0],
                    [11, 125, 0],
                    [10, 125, 0],
                    [9, 125, 0],
                    [8, 125, 0],
                    [7, 125, 0],
                    [7, 250, 0],
                    [0, 0, 0],
                    [-1, 0, 0],
                    [-1, 0, 0],
                    [-1, 0, 0],
                    [-1, 0, 0],
                    [-1, 0, 0],
                    [-1, 0, 0],
                    [-1, 0, 0],
                    [-1, 0, 0]],
            "sx1301_conf":[{"radio_0":{"enable":True,"freq":867500000},"radio_1":{"enable":True,"freq":868500000},
            "chan_multiSF_0": {"enable": True,"radio": 1,"if": -400000},
            "chan_multiSF_1": {"enable": True,"radio": 1,"if": -200000},
            "chan_multiSF_2": {"enable": True,"radio": 1,"if": 0},
            "chan_multiSF_3": {"enable": True,"radio": 0,"if": -400000},
            "chan_multiSF_4": {"enable": True,"radio": 0,"if": -200000},
            "chan_multiSF_5": {"enable": True,"radio": 0,"if": 0},
            "chan_multiSF_6": {"enable": True,"radio": 0,"if": 200000},
            "chan_multiSF_7": {"enable": True,"radio": 0,"if": 400000},
            "chan_Lora_std":  {"enable": True,"radio": 1,"if": -200000,"bandwidth": 250000,"spread_factor": 7},
            "chan_FSK":       {"enable": True,"radio": 1,"if": 300000,"bandwidth": 125000,"datarate": 50000}}]
            }


"""
 ******************************************************************************
 ********************************** WARNING ***********************************
 ******************************************************************************
  The implementation supports both 1.0.x and 1.1.x LoRaWAN 
  versions of the specification.
  Thus it has been decided to use the 1.1.x keys and EUI name definitions.
  The below table shows the names equivalence between versions:
               +-------------------+-------------------------+
               |       1.0.x       |          1.1.x          |
               +===================+=========================+
               | LORAWAN_DEVICE_EUI| LORAWAN_DEVICE_EUI      |
               +-------------------+-------------------------+
               | LORAWAN_APP_EUI   | LORAWAN_JOIN_EUI        |
               +-------------------+-------------------------+
               | N/A               | LORAWAN_APP_KEY         |
               +-------------------+-------------------------+
               | LORAWAN_APP_KEY   | LORAWAN_NWK_KEY         |
               +-------------------+-------------------------+
               | LORAWAN_NWK_S_KEY | LORAWAN_F_NWK_S_INT_KEY |
               +-------------------+-------------------------+
               | LORAWAN_NWK_S_KEY | LORAWAN_S_NWK_S_INT_KEY |
               +-------------------+-------------------------+
               | LORAWAN_NWK_S_KEY | LORAWAN_NWK_S_ENC_KEY   |
               +-------------------+-------------------------+
               | LORAWAN_APP_S_KEY | LORAWAN_APP_S_KEY       |
               +-------------------+-------------------------+
 ******************************************************************************
 ******************************************************************************
 ******************************************************************************
"""