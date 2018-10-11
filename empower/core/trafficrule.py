#!/usr/bin/env python3
#
# Copyright (c) 2018 Roberto Riggio
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

"""EmPOWER traffic rule class."""


class TrafficRule:
    """TrafficRule class

    Traffic rules are identified by an OpenFlow match rule. A traffic rule
    points to one and only one Traffic Rule Queue. However different traffic
    rules can point to the same Traffic Rule Queue.

    Conversely, the TrafficRule is a way to match a portion of the traffic to
    a certain traffic rule queue. Developers can create new TrafficRule
    instance within a Tenant.
    """

    def __init__(self, tenant, match, dscp, label, priority=0):

        self.tenant = tenant
        self.match = match
        self.dscp = dscp
        self.label = label
        self.priority = int(priority)

    def to_dict(self):
        """Return a json-frinedly representation of the object."""

        return {'match': self.match,
                'dscp': self.dscp,
                'tenant': self.tenant.tenant_id,
                'priority': self.priority,
                'label': self.label}

    def __repr__(self):

        return "%s-%s -> %s (priority %d)" % \
            (self.tenant.tenant_id, self.dscp, self.match, self.priority)
