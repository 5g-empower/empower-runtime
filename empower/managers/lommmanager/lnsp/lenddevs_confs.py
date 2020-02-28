#!/usr/bin/env python3
#
# Copyright (c) 2020 Fondazione Bruno Kessler
# Author(s): Cristina Costa (ccosta@fbk.eu)
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
"""End Devices configurations"""

LEND_DEVS = {
    "00:28:a1:54:b8:91:72:d2":{  # DevEUI
        "devEUI":"00:28:a1:54:b8:91:72:d2",
        "label":"micro-node",
        "joinEUI":"70B3D57ED0010747".upper(),
        "activation":"ABP",
        "devAddr":"2601164F".upper(),
        "nwkSKey":"54B284286378A1A9F174E6A27946E9D0",
        "appSKey":"50E5598611EA7992680ECD92C1A9943E",
        "status":0, # 0 Never Seen, 1 Online...
        "framesUp":0, # Counter
        "framesDn":0, # Counter
        "FCntWidth":"16bit", # 16bit or 32bit
        "FCntChecks":True,
        "location":[46.06935817,11.15086417],
        "alt":400,
        "payloadFormat":"CayenneLPP"
    },
    "00:04:a3:0b:00:1b:ae:6b":{  # DevEUI
        "devEUI":"00:04:a3:0b:00:1b:ae:6b",
        "label":"my_ttu",
        "activation":"OTAA",
        "joinEUI":"70B3D57ED0010747".upper(),
        "nwkKey":"D8823E63C25FCF11E33C38B5DF2900D9",
        "devAddr":"260124FE".upper(),
        "nwkSKey":"A4A7777BF7E9B95251EC4273F27888C0",
        "appSKey":"4097AEB4ABEE78011A508C55F54700AE",
        "JoinNonce":None, # Probably not needed
        "NetID":"000001", # use 0x000000 or 0x000001 (experimental)
        "status":0, # 0 Never Seen, 1 Online...
        "framesUp":0, # Counter
        "framesDn":0, # Counter
        "FCntWidth":"16bit", # 16bit or 32bit
        "FCntChecks":True,
        "location":[46.08045020,11.26008817],
        "alt":678,
        "payloadFormat":"Proprietary"
    }
}