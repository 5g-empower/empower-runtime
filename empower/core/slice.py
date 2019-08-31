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

import logging
import json

from empower.core.etheraddress import EtherAddress

WIFI_SLICE_SCHEDULER_RR = 0
WIFI_SLICE_SCHEDULER_DRR = 1
WIFI_SLICE_SCHEDULER_ADRR = 2

WIFI_SLICE_SCHEDULERS = {
    WIFI_SLICE_SCHEDULER_RR: 'ROUND_ROBIN',
    WIFI_SLICE_SCHEDULER_DRR: 'DEFICIT_ROUND_ROBIN',
    WIFI_SLICE_SCHEDULER_ADRR: 'AIRTIME_DEFICIT_ROUND_ROBIN'
}

UE_SLICE_SCHEDULER_RR = 0

UE_SLICE_SCHEDULERS = {
    UE_SLICE_SCHEDULER_RR: 'ROUND_ROBIN'
}


class Slice:
    """EmPOWER Slice Class."""

    default_properties = {}

    def __init__(self, slice_id, properties=None, devices=None):

        # set read-only parameters
        self.slice_id = int(slice_id)

        # logger :)
        self.log = logging.getLogger(self.__class__.__module__)

        # parse properties
        self.properties = self._parse_properties(properties)

        # parse per device properties
        self.devices = {}
        if devices:
            for device in devices:
                self.devices[EtherAddress(device)] = \
                    self._parse_properties(devices[device])

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        desc = {
            'slice_id': self.slice_id,
            'properties': self.properties,
            'devices': self.devices
        }

        return desc

    def _parse_properties(self, _):

        return self.default_properties

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "%s" % self.slice_id

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.slice_id)

    def __eq__(self, other):
        if isinstance(other, WiFiSlice):
            return self.slice_id == other.slice_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"


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


class LTESlice(Slice):
    """EmPOWER LTE Slice Class."""

    default_properties = {
        'rbgs': 5,
        'ue_scheduler': UE_SLICE_SCHEDULER_RR
    }

    def to_str(self):
        """Return an ASCII representation of the object."""

        msg = "[LTE] id %s rbgs %s ue_scheduler %s"

        return msg % (self.slice_id,
                      self.properties['rbgs'],
                      UE_SLICE_SCHEDULERS[self.properties['ue_scheduler']])

    def _parse_properties(self, descriptor=None):

        properties = {**self.default_properties}

        if not descriptor:
            return properties

        if 'rbgs' in descriptor:

            rbgs = descriptor['rbgs']

            if isinstance(rbgs, int):
                properties['rbgs'] = rbgs
            else:
                properties['rbgs'] = int(rbgs)

        if 'ue_scheduler' in descriptor:

            ue_scheduler = descriptor['ue_scheduler']

            if not isinstance(ue_scheduler, int):
                ue_scheduler = int(ue_scheduler)

            if ue_scheduler not in UE_SLICE_SCHEDULERS:
                raise ValueError("Invalid UE slice scheduler %u" %
                                 ue_scheduler)

            properties['ue_scheduler'] = ue_scheduler

        return properties
