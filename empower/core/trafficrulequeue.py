#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

"""Traffic rule."""


from empower.datatypes.etheraddress import EtherAddress


class TrafficRuleQueue(object):
    """EmPOWER traffic rule queue.

    A traffic rule is essentially a queue that is dynamically created at a
    certain WTP in order to collect a portion of the flowspace belonging to a
    given tenant. For example, a tenant can decide to create a default traffic
    rule plus a traffic rule for all the HTTP packets (tp_dst=80)

    Attributes:
        dscp: the traffic label (as an int)
        ssid: the tenant's ssid (as an SSID object)
        amsdu_aggregation: indicates if the traffic of this queue is going to
          be aggregated in A-MSDUs according to 802.11n settings
        quantum: the quantum to be assigned to this queue at each round
    """
    def __init__(self, ssid, dscp, block):

        self.ssid = ssid
        self.dscp = dscp
        self.block = block
        self._quantum = 12000
        self._amsdu_aggregation = False

    def to_dict(self):
        """Return a json-frinedly representation of the object."""

        return {'ssid': self.ssid,
                'dscp': self.dscp,
                'amsdu_aggregation': self.amsdu_aggregation,
                'quantum': self.quantum}

    def __repr__(self):

        return "%s-%s quantum %u amsdu_aggreagation %s" % \
            (self.ssid, self.dscp, self.quantum, self._amsdu_aggregation)

    @property
    def amsdu_aggregation(self):
        """ Get amsdu_aggregation. """

        return self._amsdu_aggregation

    @amsdu_aggregation.setter
    def amsdu_aggregation(self, amsdu_aggregation):
        """ Set amsdu_aggregation. """

        self._amsdu_aggregation = bool(amsdu_aggregation)

        self.block.radio.connection.send_set_traffic_rule(self)

    @property
    def quantum(self):
        """ Get quantum . """

        return self._quantum

    @quantum.setter
    def quantum(self, quantum):
        """ Set quantum . """

        self._quantum = int(quantum)

        self.block.radio.connection.send_set_traffic_rule(self)
