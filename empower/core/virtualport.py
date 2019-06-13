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

from uuid import uuid4

from empower.datatypes.match import Match
from empower.core.utils import get_module

import empower.logger
LOG = empower.logger.get_logger()


class VirtualPortProp(dict):
    """Virtual port class (dictionary)."""

    def __init__(self, endpoint, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = endpoint

    def __delitem__(self, key):
        """Clear virtual port and update/remove intent."""

        # delete all outgoing virtual links
        self[key].clear()

        # remove old entry
        dict.__delitem__(self, key)

        if self.items():
            self._update_intent()
        else:
            self._remove_intent(self.endpoint.uuid)

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

    @classmethod
    def _remove_intent(cls, uuid):
        """Remove intent."""

        from empower.ibnp.ibnpserver import IBNPServer
        ibnp_server = get_module(IBNPServer.__module__)
        if ibnp_server and ibnp_server.connection:
            ibnp_server.connection.send_remove_endpoint(uuid)

    def _update_intent(self):
        """Set/update intent."""

        endpoint_ports = {}

        for vport_id, vport in self.items():
            props = {'dont_learn': vport.dont_learn}
            endpoint_ports[vport_id] = {'port_no': vport.network_port.port_id,
                                        'properties': props}

        intent = {'version': '1.0',
                  'uuid': self.endpoint.uuid,
                  'dpid': self.endpoint.datapath.dpid,
                  'ports': endpoint_ports}

        from empower.ibnp.ibnpserver import IBNPServer
        ibnp_server = get_module(IBNPServer.__module__)
        if ibnp_server and ibnp_server.connection:
            ibnp_server.connection.send_update_endpoint(intent)

    def clear(self):
        for key in list(self.keys()):
            self.__delitem__(key)


class VirtualPort:
    """Virtual port."""

    def __init__(self, endpoint, network_port, virtual_port_id=0):

        self.endpoint = endpoint
        self.network_port = network_port
        self.virtual_port_id = virtual_port_id
        self.dont_learn = []
        self.next = VirtualPortNextProp(self)

    def clear(self):
        """Clear all outgoing links."""

        if not self.next:
            return

        self.next.clear()

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Port """

        return {'virtual_port_id': self.virtual_port_id,
                'network_port': self.network_port,
                'dont_learn': self.dont_learn}

    def __hash__(self):

        return hash(self.endpoint.endpoint_id) \
               + hash(self.virtual_port_id)

    def __eq__(self, other):

        return (other.endpoint.endpoint_id == self.endpoint.endpoint_id and
                other.virtual_port_id == self.virtual_port_id and
                other.network_port == self.network_port and
                other.dont_learn == self.dont_learn)

    def __repr__(self):

        return "endpoint_uuid %s virtual_port %u " \
               "network_port %s dont_learn %s" % \
               (self.endpoint.endpoint_id, self.virtual_port_id,
                str(self.network_port), self.dont_learn)


class VirtualPortNextProp(dict):
    """Chaining class."""

    def __init__(self, my_virtual_port):
        super(VirtualPortNextProp, self).__init__()
        self.my_virtual_port = my_virtual_port
        self.__uuids__ = {}

    def __delitem__(self, key):
        """Clear virtual port configuration."""

        from empower.ibnp.ibnpserver import IBNPServer
        ibnp_server = get_module(IBNPServer.__module__)

        # remove virtual links
        if key in self.__uuids__:
            if ibnp_server.connection:
                ibnp_server.connection.send_remove_rule(self.__uuids__[key])
            else:
                LOG.warning('IBN not available')

            self.my_virtual_port.network_port.remove_match(self.__uuids__[key])

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

        self.__uuids__[key] = None

        from empower.ibnp.ibnpserver import IBNPServer
        ibnp_server = get_module(IBNPServer.__module__)

        rule_uuid = uuid4()

        match = Match(key)
        self.my_virtual_port.network_port.add_match(match, rule_uuid)

        priority = None
        if 'priority' in match.match:
            priority = int(match.match['priority'])
            del match.match['priority']

        # set/update intent
        intent = {'version': '1.0',
                  'uuid': rule_uuid,
                  'ttp_uuid': value.endpoint.uuid,
                  'ttp_vport': value.virtual_port_id,
                  'stp_uuid': self.my_virtual_port.endpoint.uuid,
                  'stp_vport': self.my_virtual_port.virtual_port_id,
                  'match': match.match}

        # custom priorities start at 250 in Ryu, the priority value is summed
        if priority is not None:
            intent['priority'] = priority

        # add new virtual link
        if key in self.__uuids__:
            if ibnp_server.connection:
                ibnp_server.connection.send_add_rule(intent)
            else:
                LOG.warning('IBN not available')
        self.__uuids__[key] = rule_uuid

        # add entry
        dict.__setitem__(self, key, value)

    def clear(self):
        for key in list(self.keys()):
            self.__delitem__(key)
