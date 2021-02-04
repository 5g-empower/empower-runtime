#!/usr/bin/env python3
#
# Copyright (c) 2022 Roberto Riggio
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

"""Bitrate predictor app."""

import enum

from empower_core.app import EVERY


MANIFEST = {
    "label": "Bitrate predictor app",
    "desc": "Predicts bitrate starting from RSRP/RSRQ measurements",
    "modules": ['vbsp'],
    "callbacks": {
        "default": "Called when new predictions are available"
    },
    "params": {
        "imsi": {
            "desc": "The UE to monitor.",
            "mandatory": True,
            "type": "IMSI",
            "static": True
        }
    }
}
