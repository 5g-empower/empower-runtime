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

"""Network port."""

from empower.core.utils import ofmatch_s2d
from empower.main import RUNTIME

class NetworkPort():
    """Network Port."""

    def __init__(self, dp, port_id, hwaddr, iface):

        self.dp = dp
        self.port_id = port_id
        self.hwaddr = hwaddr
        self.iface = iface
        self.neighbour = None

        self._matches = {}

    def add_match(self, match, rule_uuid):

        if 'in_port' in match:
            raise ValueError('the \"in_port\" parameter is not allowed')

        # todo check for OF conflicts
        if False:
            raise ValueError('match conflict')

        self._matches[rule_uuid] = match

    def remove_match(self, rule_uuid):

        del self._matches[rule_uuid]

    def to_dict_no_neighbour(self):

        return {'dpid': self.dp.dpid,
                'port_id': self.port_id,
                'hwaddr': self.hwaddr,
                'iface': self.iface}

    def to_dict(self):
        """Return JSON representation of the object."""

        out = self.to_dict_no_neighbour()
        if self.neighbour:
            out['neighbour'] = self.neighbour.to_dict_no_neighbour()
        else:
            out['neighbour'] = None

        return out

    def __hash__(self):

        return hash(self.dp.dpid) + hash(self.port_id)

    def __eq__(self, other):

        return other.dp.dpid == self.dp.dpid and other.port_id == self.port_id

    def __repr__(self):

        out = "%s port_id %u hwaddr %s iface %s neighbour %s" % (self.dp.dpid,
                                                                 self.port_id,
                                                                 self.hwaddr,
                                                                 self.iface,
                                                                 self.neighbour)
        return out
