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

"""EmPOWER Slice Class."""

import json

from empower.managers.ranmanager.slice import Slice

WIFI_SLICE_SCHEDULER_RR = 0
WIFI_SLICE_SCHEDULER_DRR = 1
WIFI_SLICE_SCHEDULER_ADRR = 2

WIFI_SLICE_SCHEDULERS = {
    WIFI_SLICE_SCHEDULER_RR: 'ROUND_ROBIN',
    WIFI_SLICE_SCHEDULER_DRR: 'DEFICIT_ROUND_ROBIN',
    WIFI_SLICE_SCHEDULER_ADRR: 'AIRTIME_DEFICIT_ROUND_ROBIN'
}


class WiFiSlice(Slice):
    """EmPOWER Wi-Fi Slice Class."""

    default_properties = {
        'amsdu_aggregation': False,
        'quantum': 12000,
        'sta_scheduler': WIFI_SLICE_SCHEDULER_RR
    }

    def to_str(self):
        """Return an ASCII representation of the object."""

        msg = "[Wi-Fi] id %s amsdu_aggregation %s quantum %s sta_scheduler %s"

        return msg % (self.slice_id,
                      self.properties['amsdu_aggregation'],
                      self.properties['quantum'],
                      WIFI_SLICE_SCHEDULERS[self.properties['sta_scheduler']])

    def _parse_properties(self, descriptor=None):

        properties = {**self.default_properties}

        if not descriptor:
            return properties

        if 'amsdu_aggregation' in descriptor:

            amsdu_aggregation = descriptor['amsdu_aggregation']

            if not isinstance(amsdu_aggregation, bool):
                amsdu_aggregation = json.loads(amsdu_aggregation.lower())

            properties['amsdu_aggregation'] = amsdu_aggregation

        if 'quantum' in descriptor:

            quantum = descriptor['quantum']

            if isinstance(quantum, int):
                properties['quantum'] = quantum
            else:
                properties['quantum'] = int(quantum)

        if 'sta_scheduler' in descriptor:

            sta_scheduler = descriptor['sta_scheduler']

            if not isinstance(sta_scheduler, int):
                sta_scheduler = int(sta_scheduler)

            if sta_scheduler not in WIFI_SLICE_SCHEDULERS:
                raise ValueError("Invalid Wi-Fi slice scheduler %u" %
                                 sta_scheduler)

            properties['sta_scheduler'] = sta_scheduler

        return properties
