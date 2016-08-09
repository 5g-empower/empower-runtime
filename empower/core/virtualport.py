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


class VirtualPort(object):
    """Virtual port."""

    def __init__(self, dpid, ovs_port_id, virtual_port_id, hwaddr, iface):

        self.dpid = dpid
        self.ovs_port_id = ovs_port_id
        self.virtual_port_id = virtual_port_id
        self.hwaddr = hwaddr
        self.iface = iface

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
    """ Virtual port associated to an LVAP."""

    def __init__(self, dpid, ovs_port_id, virtual_port_id, hwaddr, iface):

        self.dpid = dpid
        self.ovs_port_id = ovs_port_id
        self.virtual_port_id = virtual_port_id
        self.hwaddr = hwaddr
        self.iface = iface
        self.next = VirtualPortPropLvap()


class VirtualPortLvnf(VirtualPort):
    """ Virtual port associated to an LVAP."""

    def __init__(self, dpid, ovs_port_id, virtual_port_id, hwaddr, iface):

        self.dpid = dpid
        self.ovs_port_id = ovs_port_id
        self.virtual_port_id = virtual_port_id
        self.hwaddr = hwaddr
        self.iface = iface
        self.next = VirtualPortPropLvnf()


class VirtualPortProp(dict):
    """VirtualPortProp class.

    This maps Flows to VirtualPorts. Notice that the current implementation
    only supports chaining of LVAPs with other LVNFs. Chaining of two LVNFs is
    not implemented yet.
    """

    def __init__(self):
        super(VirtualPortProp, self).__init__()
        self.__uuids__ = {}

    def __delitem__(self, key):
        """Clear virtual port configuration.

        Remove entry from dictionary and remove flows.
        """

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        match = key_to_match(key)

        # remove virtual links
        if match in self.__uuids__:
            del_intent(self.__uuids__[match])
            del self.__uuids__[match]

        # remove old entry
        dict.__delitem__(self, match)

    @property
    def uuids(self):
        """Return list of uuids."""

        return self.__uuids__

    def __getitem__(self, key):
        """Return next virtual port.

        Accepts as an input a dictionary with the openflow match rule for
        the virtual port. Example:

        key = {"dl_src": "aa:bb:cc:dd:ee:ff"}
        """

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        match = key_to_match(key)
        return dict.__getitem__(self, match)

    def __contains__(self, key):
        """Check if entry exists.

        Accepts as an input a dictionary with the openflow match rule for
        the virtual port. Example:

        key = {"dl_src": "aa:bb:cc:dd:ee:ff"}
        """

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        match = key_to_match(key)

        return dict.__contains__(self, match)


class VirtualPortPropLvap(VirtualPortProp):
    """VirtualPortProp class for LVAPs."""

    def __init__(self):
        super(VirtualPortPropLvap, self).__init__()
        self.lvap = None


class VirtualPortPropLvnf(VirtualPortProp):
    """VirtualPortProp class for LVAPs."""

    def __init__(self):
        super().__init__()
        self.lvnf = None
