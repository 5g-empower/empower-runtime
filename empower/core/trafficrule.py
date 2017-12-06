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


def ofmatch_d2s(key):
    """Convert an OFMatch from dictionary to string."""

    match = ",".join(["%s=%s" % x for x in sorted(key.items())])
    return match


def ofmatch_s2d(match):
    """Convert an OFMatch from string to dictionary."""

    key = {}

    if match == "":
        return key

    for token in match.split(","):
        key_t, value_t = token.split("=")

        if key_t == 'dl_vlan':
            value_t = int(value_t)

        if key_t == 'dl_type':
            value_t = int(value_t, 16)

        if key_t == 'in_port':
            value_t = int(value_t)

        if key_t == 'nw_proto':
            value_t = int(value_t, 16)

        if key_t == 'tp_dst':
            value_t = int(value_t)

        if key_t == 'tp_src':
            value_t = int(value_t)

        key[key_t] = value_t

    return key


class TrafficRule(object):
    """EmPOWER traffic rule.

    A traffic rule is essentially a queue that is dynamically created at a
    certain WTP in order to collect a portion of the flowspace belonging to a
    given tenant. For example, a tenant can decide to create a default traffic
    rule plus a traffic rule for all the HTTP packets (tp_dst=80)

    Attributes:
        dscp: the traffic label
        tenant: the tenant
        amsdu_aggregation: indicates if the traffic of this queue is going to
          be aggregated in A-MSDUs according to 802.11n settings
        quantum: the quantum to be assigned to this queue at each round
    """
    def __init__(self, tenant, match, dscp=0, quantum=1500,
                 amsdu_aggregation=False):

        self.tenant = tenant
        self.match = match
        self.dscp = dscp
        self.quantum = quantum
        self.amsdu_aggregation = amsdu_aggregation

    def to_dict(self):
        """Return a json-frinedly representation of the object."""

        return {'dscp': self.dscp,
                'match': self.match,
                'tenant_id': self.tenant.tenant_id,
                'amsdu_aggregation': self.amsdu_aggregation,
                'quantum': self.quantum}

    @property
    def amsdu_aggregation(self):
        """ Get amsdu_aggregation. """

        return self._amsdu_aggregation

    @amsdu_aggregation.setter
    def amsdu_aggregation(self, amsdu_aggregation):
        """ Set amsdu_aggregation. """

        self._amsdu_aggregation = bool(amsdu_aggregation)

    @property
    def quantum(self):
        """ Get quantum . """

        return self._quantum

    @quantum.setter
    def quantum(self, quantum):
        """ Set quantum . """

        if isinstance(quantum, str):
            quantum = int(quantum)

        self._quantum = int(quantum)

    @property
    def dscp(self):
        """ Get dscp . """

        return self._dscp

    @dscp.setter
    def dscp(self, dscp):
        """ Set dscp . """

        if isinstance(dscp, str):
            dscp = int(dscp, 16)

        self._dscp = dscp

    def __eq__(self, other):

        return (other.tenant == self.tenant and other.dscp == self.dscp)

    def __repr__(self):

        return "%s -> (dscp %u, quantum %u)" % \
            (self.match, self.dscp, self.quantum)


class TrafficRuleProp(dict):
    """Maps Flows to TrafficRules."""

    def __init__(self):
        super(TrafficRuleProp, self).__init__()
        self.__uuids__ = {}

    def __delitem__(self, key):
        """Clear traffic rule configuration."""

        value = self.__getitem__(key)

        # remove queues
        from empower.main import RUNTIME
        from empower.intentserver.intentserver import IntentServer
        intent_server = RUNTIME.components[IntentServer.__module__]

        wtps = RUNTIME.tenants[value.tenant.tenant_id].wtps.values()

        for wtp in wtps:

            if not wtp.is_online():
                continue

            # delete queue on wtp
            wtp.connection.send_del_traffic_rule(value)

        # remove traffic rules
        if key in self.__uuids__:
            for uuid in self.__uuids__[key]:
                intent_server.remove_traffic_rule(uuid)
            del self.__uuids__[key]

        # remove old entry
        dict.__delitem__(self, key)

    def __setitem__(self, key, value):
        """Set traffic rule configuration."""

        if value and not isinstance(value, TrafficRule):
            raise KeyError("Expected TrafficRule, got %s" % type(key))

        # remove traffic rule
        if self.__contains__(key):
            self.__delitem__(key)

        self.__uuids__[key] = []

        from empower.main import RUNTIME
        from empower.intentserver.intentserver import IntentServer
        intent_server = RUNTIME.components[IntentServer.__module__]

        wtps = RUNTIME.tenants[value.tenant.tenant_id].wtps.values()

        for wtp in wtps:

            if not wtp.is_online():
                continue

            # get network port
            port = wtp.port()

            # set/update traffic rule
            intent = {'version': '1.0',
                      'dpid': port.dpid,
                      'port': port.port_id,
                      'dscp': value.dscp,
                      'match': ofmatch_s2d(key)}

            # add new virtual link
            uuid = intent_server.add_traffic_rule(intent)
            self.__uuids__[key].append(uuid)

            # create queue on wtp
            wtp.connection.send_add_traffic_rule(value)

        # add entry
        dict.__setitem__(self, key, value)