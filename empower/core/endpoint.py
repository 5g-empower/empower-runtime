#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""Endpoint."""


from empower.core.virtualport import VirtualPortProp


class Endpoint:
    """An endpoint."""

    def __init__(self, uuid, label="", datapath=None):

        self.uuid = uuid
        self.label = label
        self.datapath = datapath
        self.ports = VirtualPortProp(self)

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the Endpoint."""

        return {"uuid": self.uuid,
                "label": self.label,
                "datapath": self.datapath,
                "ports": self.ports}

    def __eq__(self, other):

        if isinstance(other, Endpoint):
            return self.uuid == other.uuid

        return False

    def __str__(self):

        return "Endpoint %s, label=%s, ports=%s" \
               % (self.uuid, self.label, self.ports)
