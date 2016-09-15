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

"""VBS Stats Module."""

from empower.vbsp.messages import statistics_pb2
from empower.vbsp.messages import configs_pb2

PRT_VBSP_RRC_STATS = "mRRC_meas"

RRC_STATS_RAT_TYPE = {
    "EUTRA": statistics_pb2.RAT_EUTRA
}

RRC_STATS_REPORT_CONF_TYPE = [
                        "periodical_ref_signal", "A1", "A2", "A3", "A4", "A5"]

RRC_STATS_EVENT_THRESHOLD_TYPE = ["RSRP", "RSRQ"]

RRC_STATS_TRIGGER_QUANT = {
    "RSRP": configs_pb2.TRIGQ_RSRP,
    "RSRQ": configs_pb2.TRIGQ_RSRQ
}

RRC_STATS_REPORT_INTR = {
    1: configs_pb2.REPINT_ms1024,
    2: configs_pb2.REPINT_ms2048,
    5: configs_pb2.REPINT_ms5120,
    10: configs_pb2.REPINT_ms10240,
    60: configs_pb2.REPINT_min1,
    360: configs_pb2.REPINT_min6,
    720: configs_pb2.REPINT_min12,
    1800: configs_pb2.REPINT_min30,
    3600: configs_pb2.REPINT_min60
}

RRC_STATS_NUM_REPORTS = {
    1: configs_pb2.REPAMT_1,
    2: configs_pb2.REPAMT_2,
    4: configs_pb2.REPAMT_4,
    8: configs_pb2.REPAMT_8,
    16: configs_pb2.REPAMT_16,
    32: configs_pb2.REPAMT_32,
    64: configs_pb2.REPAMT_64,
    "infinite": configs_pb2.REPAMT_infinity
}

RRC_STATS_BW = {
    6: configs_pb2.AMBW_6,
    15: configs_pb2.AMBW_15,
    25: configs_pb2.AMBW_25,
    50: configs_pb2.AMBW_50,
    75: configs_pb2.AMBW_75,
    100: configs_pb2.AMBW_100
}


