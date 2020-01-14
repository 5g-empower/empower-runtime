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

from empower.managers.ranmanager.slice import Slice

UE_SLICE_SCHEDULER_RR = 0

UE_SLICE_SCHEDULERS = {
    UE_SLICE_SCHEDULER_RR: 'ROUND_ROBIN'
}


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
