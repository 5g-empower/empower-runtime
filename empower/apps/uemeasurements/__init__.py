#!/usr/bin/env python3
#
# Copyright (c) 2020 Roberto Riggio
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

"""UE Measurements."""

import enum

from empower_core.app import EVERY


class RRCReportInterval(enum.Enum):
    MS120 = 0
    MS240 = 1
    MS480 = 2
    MS640 = 3
    MS1024 = 4
    MS2048 = 5
    MS5120 = 6
    MS10240 = 7
    MIN1 = 8
    MIN6 = 9
    MIN12 = 10
    MIN30 = 11
    MIN60 = 12


class RRCReportAmount(enum.Enum):
    R1 = 0
    R2 = 1
    R4 = 2
    R8 = 3
    R16 = 4
    R32 = 5
    R64 = 6
    INFINITY = 7


MANIFEST = {
    "label": "UE Measurements",
    "desc": "Start UE Measurements for serving cell",
    "modules": ['vbsp'],
    "callbacks": {
        "default": "Called when new measurements are available"
    },
    "params": {
        "imsi": {
            "desc": "The UE to monitor.",
            "mandatory": True,
            "type": "IMSI",
            "static": True
        },
        "meas_id": {
            "desc": "The id of the measurement to be created.",
            "mandatory": True,
            "default": 1,
            "type": list(range(1, 33)),
            "static": True
        },
        "interval": {
            "desc": "The control UE reporting interval.",
            "mandatory": True,
            "default": RRCReportInterval.MS240.name,
            "type": [e.name for e in RRCReportInterval]
        },
        "amount": {
            "desc": "The control UE reporting interval.",
            "mandatory": True,
            "default": RRCReportAmount.INFINITY.name,
            "type": [e.name for e in RRCReportAmount]
        },
    }
}
