#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Virtual port."""

from empower.datatypes.etheraddress import EtherAddress


class VirtualPort():

    def __init__(self, dpid, ovs_port_id, virtual_port_id, hwaddr, iface):

        self.dpid = dpid
        self.ovs_port_id = ovs_port_id
        self.virtual_port_id = virtual_port_id
        self.hwaddr = hwaddr
        self.iface = iface
        self.next = VirtualPortProp()

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


class VirtualPortProp(dict):
    """VirtualPortProp class.

    This maps Flows to VirtualPorts. Notice that the current implementation
    only supports chaining of LVAPs with other LVNFs. Chaining of two LVNFs is
    not implemented yet.
    """

    def __delitem__(self, key):
        """Clear virtual port configuration.

        Remove entry from dictionary and remove flows.
        """

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        match = ";".join(["%s=%s" % (k, v) for k, v in key.items()])

        # remove old entry
        dict.__delitem__(self, match)

        # set flows
        if hasattr(self, 'lvap') and self.lvap:
            self.lvap.encap = EtherAddress("00:00:00:00:00:00")

    def __setitem__(self, key, value):
        """Set virtual port configuration.

        Accepts as an input a dictionary with the openflow match rule for
        this virtual port. Example:

        key = {"dl_src"= "aa:bb:cc:dd:ee:ff"}
        """

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        if not isinstance(value, VirtualPort):
            raise KeyError("Expected VirtualPort, got %s" % type(key))

        match = ";".join(["%s=%s" % (k, v) for k, v in key.items()])

        # the block is found, update the port
        if self.__contains__(key):
            self.__delitem__(key)

        # update dict
        dict.__setitem__(self, match, value)

        # set flows
        if hasattr(self, 'lvap') and self.lvap:
            self.lvap.encap = value.hwaddr

    def __getitem__(self, key):

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        match = ";".join(["%s=%s" % (k, v) for k, v in key.items()])
        return dict.__getitem__(self, match)

    def __contains__(self, key):

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        match = ";".join(["%s=%s" % (k, v) for k, v in key.items()])
        return dict.__contains__(self, match)
