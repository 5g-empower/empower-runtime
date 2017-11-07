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

"""EmPOWER Traffic Rule."""


class TrafficRule(object):
    """ EmPOWER traffic rule.

    It defines the management rules for a traffyc type to be considered for
    the queues management in the WTPs

    Attributes:
        dscp: the traffic label
        tenant: the tenant
        amsdu_aggregation: indicates if the traffic of this queue is going to
          be aggregated in A-MSDUs according to 802.11n settings
        ampdu_aggregation: indicates if the traffic of this queue is going to
          be aggregated in A-MPDUs according to 802.11n settings
        priority: the priority of the traffic rule
        parent_priority: the overal tenant priority
    """
    def __init__(self, tenant, dscp=0, priority=100, parent_priority=100,
                 amsdu_aggregation=True, ampdu_aggregation=True):

        self._tenant = tenant
        self._amsdu_aggregation = amsdu_aggregation
        self._ampdu_aggregation = ampdu_aggregation
        self._priority = priority
        self._parent_priority = parent_priority
        self._dscp = dscp

    def to_dict(self):
        """Return a json-frinedly representation of the object."""

        return {'dscp': self.dscp,
                'tenant': self.tenant,
                'amsdu_aggregation': self.amsdu_aggregation,
                'ampdu_aggregation': self.ampdu_aggregation,
                'priority': self.priority,
                'parent_priority': self.parent_priority}

    @property
    def amsdu_aggregation(self):
        """ Get amsdu_aggregation . """

        return self._amsdu_aggregation

    @amsdu_aggregation.setter
    def amsdu_aggregation(self, amsdu_aggregation):
        """ Set amsdu_aggregation . """

        self._amsdu_aggregation = bool(amsdu_aggregation)

        # Loop over the wtps of this tenant and send the message
        # self.block.radio.connection.send_set_port(self)

    @property
    def ampdu_aggregation(self):
        """ Get ampdu_aggregation . """

        return self._ampdu_aggregation

    @ampdu_aggregation.setter
    def ampdu_aggregation(self, ampdu_aggregation):
        """ Set ampdu_aggregation . """

        self._ampdu_aggregation = bool(ampdu_aggregation)

        # Loop over the wtps of this tenant and send the message
        # self.block.radio.connection.send_set_port(self)

    @property
    def priority(self):
        """ Get priority . """

        return self._priority

    @priority.setter
    def priority(self, priority):
        """ Set priority . """

        self._priority = int(priority)

        # Loop over the wtps of this tenant and send the message
        # self.block.radio.connection.send_set_port(self)

    @property
    def parent_priority(self):
        """ Get parent_priority . """

        return self._parent_priority

    @parent_priority.setter
    def parent_priority(self, parent_priority):
        """ Set parent_priority . """

        self._parent_priority = int(parent_priority)

        # Loop over the wtps of this tenant and send the message
        # self.block.radio.connection.send_set_port(self)
