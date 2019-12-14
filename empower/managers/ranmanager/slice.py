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

from empower.core.etheraddress import EtherAddress
from empower.core.serialize import serializable_dict


@serializable_dict
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
        if isinstance(other, Slice):
            return self.slice_id == other.slice_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
