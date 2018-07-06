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

from empower.datatypes.match import Match


class TrafficRule:
    """TrafficRule class

    Traffic rules are identified by an OpenFlow match rule. A traffic rule
    points to one and only one Traffic Rule Queue. However different traffic
    rules can point to the same Traffic Rule Queue.

    Notice how TrafficRule and TrafficRuleQueue are two different concept. The
    TrafficRuleQueue exists within a certain ResourceBlock. This means that
    each interface in a WTP can have many TrafficRuleQueue instances, one for
    each type of traffic.

    Conversely, the TrafficRule is a way to match a portion of the traffic to
    a certain traffic rule queue. Developers can create new TrafficRule
    instance within a Tenant.
    """

    def __init__(self, ssid, match, dscp, label):

        self.ssid = ssid
        self.match = Match(match)
        self.dscp = dscp
        self.label = label

    def to_dict(self):
        """Return a json-frinedly representation of the object."""

        return {'match': self.match,
                'dscp': self.dscp,
                'ssid': self.ssid,
                'label': self.label}

    def __repr__(self):

        return "%s-%s -> %s" % (self.ssid, self.dscp, self.match)
