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

"""TXP Bin Counter Primitive."""

from empower.core.app import EVERY

MANIFEST = {
    "label": "TXP Bin Counter",
    "desc": "Tracks TX packets/bytes counters for a given destination address",
    "modules": ['lvapp'],
    "callbacks": {
        "default": "Called when new measurements are available"
    },
    "params": {
        "iface_id": {
            "desc": "The Wi-Fi interface.",
            "mandatory": True,
            "type": "int"
        },
        "addr": {
            "desc": "The address to monitor.",
            "mandatory": True,
            "type": "EtherAddress"
        },
        "bins": {
            "desc": "The bins for the measurements (comma separated).",
            "mandatory": False,
            "default": "8192",
            "type": "str"
        },
        "every": {
            "desc": "The control loop period (in ms).",
            "mandatory": False,
            "default": EVERY,
            "type": "int"
        }
    }
}
