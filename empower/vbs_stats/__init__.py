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

PRT_VBSP_L2_STATS_REQUEST = "l2_stats_req"
PRT_VBSP_L2_STATS_RESPONSE = "l2_stats_repl"

L2_STATS_TYPE = {
    "complete": statistics_pb2.L2ST_COMPLETE,
    "cell": statistics_pb2.L2ST_CELL,
    "ue": statistics_pb2.L2ST_UE
}

L2_STATS_REPORT_FREQ = {
    "once": statistics_pb2.REPF_ONCE,
    "periodical": statistics_pb2.REPF_PERIODICAL,
}

L2_CELL_STATS_TYPES = {
    "noise_interference": statistics_pb2.CST_NOISE_INTERFERENCE
}

L2_UE_STATS_TYPES = {
    "buffer_status_report": statistics_pb2.UEST_BSR,
    "power_headroom_report": statistics_pb2.UEST_PRH,
    "rlc_buffer_status_report": statistics_pb2.UEST_RLC_BS,
    "mac_ce_buffer_status_report": statistics_pb2.UEST_MAC_CE_BS,
    "downlink_cqi_report": statistics_pb2.UEST_DL_CQI,
    "paging_buffer_status_report": statistics_pb2.UEST_PBS,
    "uplink_cqi_report": statistics_pb2.UEST_UL_CQI
}
