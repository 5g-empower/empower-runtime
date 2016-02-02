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

from empower.core.intent import send_intent


def key_to_match(key):
    """Convert a OF match in dictionary form to a string."""

    match = ";".join(["%s=%s" % (k, v) for k, v in key.items()])
    return match


def match_to_key(match):
    """Convert a OF match string in dictionary form"""

    key = {}

    for token in match.split(";"):
        k, v = token.split("=")
        key[k] = v

    return key


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

        match = key_to_match(key)

        # remove virtual links
        # TODO: Implement

        # remove old entry
        dict.__delitem__(self, match)

    def __setitem__(self, key, value):
        """Set virtual port configuration.

        Accepts as an input a dictionary with the openflow match rule for
        the virtual port specified as value. Notice value could also be None
        in case the chain consists just in an LVAP. Example:

        key = {"dl_src": "aa:bb:cc:dd:ee:ff"}
        """

        if not isinstance(key, dict):
            raise KeyError("Expected dict, got %s" % type(key))

        if value and not isinstance(value, VirtualPort):
            raise KeyError("Expected VirtualPort, got %s" % type(key))

        if not value:

            value_hwaddr = None
            value_dpid = None
            value_ovs_port_id = None

        else:

            value_hwaddr = value.hwaddr
            value_dpid = value.dpid
            value_ovs_port_id = value.ovs_port_id

        # set flows
        if hasattr(self, 'lvap'):

            # if encap is set, then all outgoing traffic must go to THE SAME
            # LVNF. This is because the outgoing traffic will be LWAPP
            # encapsulated and as such cannot be handled anyway by OF
            # switches. Ignore totally the specified key and silently use as
            # key the LWAPP src and dst addresses. Notice that this will send
            # as many intents as the number of blocks.
            if self.lvap.encap:

                for tmp in dict(self):

                    old_key = {}

                    for token in tmp.split(";"):
                        k, v = token.split("=")
                        old_key[k] = v

                    self.__delitem__(old_key)

                # set downlink and uplink virtual link(s)
                for r_port in self.lvap.downlink.values():

                    for v_port in r_port.block.radio.ports.values():

                        if v_port.iface != "empower0":
                            continue

                        dpid = v_port.dpid
                        ovs_port_id = v_port.port_id
                        hwaddr = v_port.hwaddr

                        key = {}
                        key['dpid'] = dpid
                        key['ovs_port_id'] = ovs_port_id
                        key['dl_src'] = hwaddr
                        key['dl_dst'] = value_hwaddr

                        match = key_to_match(key)

                        intent = {'src_dpid': dpid,
                                  'src_port_id': ovs_port_id,
                                  'hwaddr': self.lvap.hwaddr,
                                  'dst_dpid': value_dpid,
                                  'dst_port_id': value_ovs_port_id,
                                  'match': match}

                        send_intent(intent)

                        dict.__setitem__(self, match, value)

                        break

                for r_port in self.lvap.uplink.values():

                    for v_port in r_port.block.radio.ports.values():

                        if v_port.iface != "empower0":
                            continue

                        dpid = v_port.dpid
                        ovs_port_id = v_port.port_id
                        hwaddr = v_port.hwaddr

                        key = {}
                        key['dpid'] = dpid
                        key['port_id'] = ovs_port_id
                        key['dl_src'] = hwaddr
                        key['dl_dst'] = value_hwaddr

                        match = key_to_match(key)

                        intent = {'src_dpid': dpid,
                                  'src_port_id': ovs_port_id,
                                  'dst_dpid': value_dpid,
                                  'dst_port_id': value_ovs_port_id,
                                  'match': match}

                        send_intent(intent)

                        dict.__setitem__(self, match, value)

                        break

            # encap is not set, then all outgoing traffic can go to different
            # LVNFs as specified by key. Remove only the key is it already
            # exists. Notice that this will send as many intents as the number
            # of blocks.
            else:

                # set downlink and uplink virtual link(s)
                for r_port in self.lvap.downlink.values():

                    for v_port in r_port.block.radio.ports.values():

                        if v_port.iface != "empower0":
                            continue

                        dpid = v_port.dpid
                        ovs_port_id = v_port.port_id
                        hwaddr = v_port.hwaddr

                        # make sure that dl_src is specified
                        key['dl_src'] = self.lvap.hwaddr

                        # add dummy fields
                        key['dpid'] = dpid
                        key['port_id'] = ovs_port_id

                        match = key_to_match(key)

                        intent = {'src_dpid': dpid,
                                  'src_port_id': ovs_port_id,
                                  'hwaddr': self.lvap.hwaddr,
                                  'dst_dpid': value_dpid,
                                  'dst_port_id': value_ovs_port_id,
                                  'match': match}

                        # remove virtual link
                        if self.__contains__(key):
                            self.__delete__(key)

                        # add new virtual link
                        send_intent(intent)

                        dict.__setitem__(self, match, value)

                        break

                for r_port in self.lvap.uplink.values():

                    for v_port in r_port.block.radio.ports.values():

                        if v_port.iface != "empower0":
                            continue

                        dpid = v_port.dpid
                        ovs_port_id = v_port.port_id
                        hwaddr = v_port.hwaddr

                        # make sure that dl_src is specified
                        key['dl_src'] = self.lvap.hwaddr

                        # add dummy fields
                        key['dpid'] = dpid
                        key['port_id'] = ovs_port_id

                        match = key_to_match(key)

                        intent = {'src_dpid': dpid,
                                  'src_port_id': ovs_port_id,
                                  'dst_dpid': value_dpid,
                                  'dst_port_id': value_ovs_port_id,
                                  'match': match}

                        # remove virtual link
                        if self.__contains__(key):
                            self.__delete__(key)

                        # add new virtual link
                        send_intent(intent)

                        dict.__setitem__(self, match, value)

                        break

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
