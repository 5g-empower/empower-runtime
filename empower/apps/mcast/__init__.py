#!/usr/bin/env python3
#
# Copyright (c) 2019 Estefania Coronado
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

"""SDN@Play Multicast Manager."""

from empower.core.app import EVERY

MANIFEST = {
    "label": "SDN@Play",
    "desc": "This application makes white bunnies happy even if watched by "
            "many people.",
    "modules": ['lvapp'],
    "params": {
        "mcast_policy": {
            "desc": "The multicast operation mode (legacy, dms, sdn@play).",
            "mandatory": False,
            "default": "sdn@play",
            "type": ["legacy", "dms", "sdn@play"]
        },
        "every": {
            "desc": "The control loop period (in ms).",
            "mandatory": False,
            "default": EVERY,
            "type": "int"
        }
    }
}
