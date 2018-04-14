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


class VirtualPortProp(dict):

    def __init__(self):
        super(VirtualPortProp, self).__init__()

    def __delitem__(self, key):
        """Clear virtual port and update/remove intent."""

        # delete all outgoing virtual links
        self[key].clear()

        endpoint_uuid = list(self.values())[0].endpoint_uuid

        # remove old entry
        dict.__delitem__(self, key)

        if self.items():
            self._update_intent()
        else:
            self._remove_intent(endpoint_uuid)

    def __setitem__(self, key, value):
        """Add virtual port and update intent."""

        if value and not isinstance(value, VirtualPort):
            raise KeyError("Expected VirtualPort, got %s" % type(key))

        # remove virtual port if exist
        if self.__contains__(key):
            self.__delitem__(key)

        # add entry
        dict.__setitem__(self, key, value)

        self._update_intent()

    def _remove_intent(self, endpoint_uuid):
        # remove intent

        intent_server = RUNTIME.components[IntentServer.__module__]
        intent_server.remove_endpoint(endpoint_uuid)

    def _update_intent(self):
        # set/update intent

        endpoint_uuid = list(self.values())[0].endpoint_uuid

        endpoint_ports = {}

        for vport_id, vport in self.items():

            endpoint_ports[vport_id] = {'hwaddr': vport.network_port.hwaddr,
                                        'dpid': vport.network_port.dpid,
                                        'port_no': vport.network_port.port_id,
                                        'learn_host': vport.learn_host}

        intent = {'version': '1.0',
                  'ports': endpoint_ports}

        intent_server = RUNTIME.components[IntentServer.__module__]

        intent_server.update_endpoint(intent, endpoint_uuid)

    def clear(self):

        for key in list(self.keys()):

            self.__delitem__(key)


class VirtualPort:
    """Virtual port."""

    def __init__(self, endpoint_uuid, network_port,
                 virtual_port_id=0, learn_host=False):

        self.endpoint_uuid = endpoint_uuid
        self.network_port = network_port
        self.virtual_port_id = virtual_port_id
        self.learn_host = learn_host

        self.next = VirtualPortNextProp(self)

    def clear(self):
        """Clear all outgoing links."""

        if not self.next:
            return

        self.next.clear()

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Port """

        return {'endpoint_uuid': self.endpoint_uuid,
                'virtual_port_id': self.virtual_port_id,
                'network_port': self.network_port,
                'learn_host': self.learn_host}

    def __hash__(self):

        return hash(self.endpoint_uuid) \
               + hash(self.virtual_port_id)

    def __eq__(self, other):

        return (other.endpoint_uuid == self.endpoint_uuid and
                other.virtual_port_id == self.virtual_port_id and
                other.network_port == self.network_port and
                other.learn_host == self.learn_host)

    def __repr__(self):

        return "endpoint_uuid %s virtual_port %u " \
               "network_port %s learn_host %s" % \
               (self.endpoint_uuid, self.virtual_port_id,
                str(self.network_port), self.learn_host)


class VirtualPortNextProp(dict):

    def __init__(self, my_virtual_port):
        super(VirtualPortNextProp, self).__init__()
        self.my_virtual_port = my_virtual_port
        self.__uuids__ = {}

    def __delitem__(self, key):
        """Clear virtual port configuration."""

        intent_server = RUNTIME.components[IntentServer.__module__]

        # remove virtual links
        if key in self.__uuids__:
            intent_server.remove_rule(self.__uuids__[key])
            self.__uuids__[key] = None

        # remove old entry
        dict.__delitem__(self, key)

    def __setitem__(self, key, value):
        """Set virtual port configuration."""

        if value and not isinstance(value, VirtualPort):
            raise KeyError("Expected VirtualPort, got %s" % type(key))

        # remove virtual link
        if self.__contains__(key):
            self.__delitem__(key)

        self.__uuids__[key] = None

        intent_server = RUNTIME.components[IntentServer.__module__]

        # set/update intent
        intent = {'version': '1.0',
                  'ttp_uuid': value.endpoint_uuid,
                  'ttp_vport': value.virtual_port_id,
                  'stp_uuid': self.my_virtual_port.endpoint_uuid,
                  'stp_vport': self.my_virtual_port.virtual_port_id,
                  'match': ofmatch_s2d(key)}

        # add new virtual link
        uuid = intent_server.add_rule(intent)
        self.__uuids__[key] = uuid

        # add entry
        dict.__setitem__(self, key, value)
