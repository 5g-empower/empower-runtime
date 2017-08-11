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

from empower.main import RUNTIME


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
            value_t = int(value_t)

        if key_t == 'tp_dst':
            value_t = int(value_t)

        if key_t == 'tp_src':
            value_t = int(value_t)

        key[key_t] = value_t

    return key


class VirtualPort(object):
    """Virtual port."""

    def __init__(self, virtual_port_id, phy_port):

        self.virtual_port_id = virtual_port_id
        self.dpid = phy_port.dpid
        self.ovs_port_id = phy_port.port_id
        self.hwaddr = phy_port.hwaddr
        self.iface = phy_port.iface
        self.next = dict()

    def clear(self):
        """Clear all outgoing links."""

        if not self.next:
            return

        for key in list(self.next):
            del self.next[key]

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Port """

        return {'dpid': self.dpid,
                'ovs_port_id': self.ovs_port_id,
                'virtual_port_id': self.virtual_port_id,
                'hwaddr': self.hwaddr,
                'iface': self.iface}

    def __hash__(self):

        return hash(self.dpid) + hash(self.ovs_port_id) + \
            hash(self.virtual_port_id)

    def __eq__(self, other):

        return (other.dpid == self.dpid and
                other.ovs_port_id == self.ovs_port_id and
                other.virtual_port_id == self.virtual_port_id)

    def __repr__(self):

        out_string = "%s ovs_port %s virtual_port %s hwaddr %s iface %s"

        out = out_string % (self.dpid, self.ovs_port_id, self.virtual_port_id,
                            self.hwaddr, self.iface)

        return out


class VirtualPortLvap(VirtualPort):
    """Virtual port."""

    def __init__(self, virtual_port_id, phy_port, lvap):
        super(VirtualPortLvap, self).__init__(virtual_port_id, phy_port)
        self.next = VirtualPortPropLvap(lvap)


class VirtualPortLvnf(VirtualPort):
    """Virtual port."""

    def __init__(self, virtual_port_id, phy_port):
        super(VirtualPortLvnf, self).__init__(virtual_port_id, phy_port)
        self.next = VirtualPortPropLvnf(self)


class VirtualPortProp(dict):
    """Maps Flows to VirtualPorts.

    Flows are dictionary keys in the following format:
        dl_src=11:22:33:44:55:66,tp_dst=80
    """

    def __init__(self, obj):
        super(VirtualPortProp, self).__init__()
        self.__uuids__ = {}
        self.obj = obj

    def __delitem__(self, key):
        """Clear virtual port configuration.

        Remove entry from dictionary and remove flows.
        """

        intent_server = RUNTIME.components[IntentServer.__module__]

        # remove virtual links
        if key in self.__uuids__:
            for uuid in self.__uuids__[key]:
                intent_server.remove_rule(uuid)
            del self.__uuids__[key]

        # remove old entry
        dict.__delitem__(self, key)


class VirtualPortPropLvap(VirtualPortProp):
    """VirtualPortProp class for LVAPs."""

    def __setitem__(self, key, value):
        """Set virtual port configuration."""

        if value and not isinstance(value, VirtualPort):
            raise KeyError("Expected VirtualPort, got %s" % type(key))

        # remove virtual link
        if self.__contains__(key):
            self.__delitem__(key)

        self.__uuids__[key] = []

        intent_server = RUNTIME.components[IntentServer.__module__]

        # Set downlink and uplink virtual link(s)
        dl_blocks = list(self.obj.downlink.values())
        ul_blocks = list(self.obj.uplink.values())
        blocks = dl_blocks + ul_blocks

        # r_port is a RadioPort object
        for r_port in blocks:

            n_port = r_port.block.radio.port()

            # set/update intent
            intent = {'version': '1.0',
                      'ttp_dpid': value.dpid,
                      'ttp_port': value.ovs_port_id,
                      'stp_dpid': n_port.dpid,
                      'stp_port': n_port.port_id,
                      'match': ofmatch_s2d(key)}

            # add new virtual link
            uuid = intent_server.add_rule(intent)
            self.__uuids__[key].append(uuid)

            # add entry
            dict.__setitem__(self, key, value)


class VirtualPortPropLvnf(VirtualPortProp):
    """VirtualPortProp class for LVAPs."""

    def __setitem__(self, key, value):
        """Set virtual port configuration."""

        if value and not isinstance(value, VirtualPort):
            raise KeyError("Expected VirtualPort, got %s" % type(key))

        # remove virtual link
        if self.__contains__(key):
            self.__delitem__(key)

        self.__uuids__[key] = []

        intent_server = RUNTIME.components[IntentServer.__module__]

        # set/update intent
        intent = {'version': '1.0',
                  'ttp_dpid': value.dpid,
                  'ttp_port': value.ovs_port_id,
                  'stp_dpid': self.obj.dpid,
                  'stp_port': self.obj.ovs_port_id,
                  'match': ofmatch_s2d(key)}

        # add new virtual link
        uuid = intent_server.add_rule(intent)
        self.__uuids__[key].append(uuid)

        # add entry
        dict.__setitem__(self, key, value)
