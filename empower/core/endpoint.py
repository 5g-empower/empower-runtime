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

    def __init__(self, endpoint_id, endpoint_name, dp, desc):

        self.endpoint_id = endpoint_id
        self.endpoint_name = endpoint_name
        self.desc = desc
        self.dp = dp
        self.ports = VirtualPortProp(self)

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the Endpoint."""

        return {"endpoint_uuid": self.endpoint_id,
                "endpoint_name": self.endpoint_name,
                "desc": self.desc,
                "dp": self.dp,
                "ports": self.ports}

    def __eq__(self, other):

        if isinstance(other, Endpoint):
            return self.endpoint_id == other.endpoint_id \
                   and self.endpoint_name == other.endpoint_name \
                   and self.ports == other.ports

        return False

    def __str__(self):

        return "Endpoint %s, name=%s, description=%s, ports=%s" \
               % (self.endpoint_id, self.endpoint_name, self.desc, self.ports)
