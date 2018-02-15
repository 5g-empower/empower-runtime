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

"""Virtual port."""


from empower.datatypes.etheraddress import EtherAddress
from empower.intentserver.intentserver import IntentServer
from empower.core.utils import ofmatch_d2s
from empower.core.utils import ofmatch_s2d

from empower.main import RUNTIME


class VirtualPort:
    """Virtual port."""

    def __init__(self, virtual_port_id):

        self.virtual_port_id = virtual_port_id
        self.poas = []
        self.next = VirtualPortProp(self.poas)

    def clear(self):
        """Clear all outgoing links."""

        if not self.next:
            return

        for key in list(self.next):
            del self.next[key]

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Port """

        return {'virtual_port_id': self.virtual_port_id,
                'poas': self.poas}

    def __hash__(self):

        return hash(self.virtual_port_id)

    def __eq__(self, other):

        return (other.virtual_port_id == self.virtual_port_id and
                other.network_port == self.network_port)

    def __repr__(self):

        poas = [str(x) for x in self.poas]
        return "virtual_port %u poas [%s]" % \
            (self.virtual_port_id, ", ".join(poas))


class VirtualPortProp(dict):
    """Maps flows to VirtualPorts."""

    def __init__(self, poas):
        super(VirtualPortProp, self).__init__()
        self.__uuids__ = {}
        self.poas = poas

    def __delitem__(self, key):
        """Clear virtual port configuration."""

        intent_server = RUNTIME.components[IntentServer.__module__]

        # remove virtual links
        if key in self.__uuids__:
            for uuid in self.__uuids__[key]:
                intent_server.remove_rule(uuid)
            del self.__uuids__[key]

        # remove old entry
        dict.__delitem__(self, key)

    def __setitem__(self, key, value):
        """Set virtual port configuration."""

        if value and not isinstance(value, VirtualPort):
            raise KeyError("Expected VirtualPort, got %s" % type(key))

        # remove virtual link
        if self.__contains__(key):
            self.__delitem__(key)

        self.__uuids__[key] = []

        intent_server = RUNTIME.components[IntentServer.__module__]

        # Send intents
        for port in self.poas:

            # set/update intent
            intent = {'version': '1.0',
                      'ttp_dpid': value.poas[0].dpid,
                      'ttp_port': value.poas[0].port_id,
                      'stp_dpid': port.dpid,
                      'stp_port': port.port_id,
                      'match': ofmatch_s2d(key)}

            # add new virtual link
            uuid = intent_server.add_rule(intent)
            self.__uuids__[key].append(uuid)

            # add entry
            dict.__setitem__(self, key, value)
