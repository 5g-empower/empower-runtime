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

"""Network port."""


class LQM(dict):

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):

        try:

            return dict.__getitem__(self, key)

        except KeyError:

            inf = {'addr': key,
                   'tx_packets': 0,
                   'rx_packets': 0,
                   'tx_bytes': 0,
                   'rx_bytes': 0,
                   'tx_bit_rate': 0,
                   'rx_bit_rate': 0,
                   'tx_pkt_rate': 0,
                   'rx_pkt_rate': 0}

            return inf


class NetworkPort():
    """Network Port."""

    def __init__(self, dpid, port_id, hwaddr, iface):

        self.dpid = dpid
        self.port_id = port_id
        self.hwaddr = hwaddr
        self.iface = iface
        self.lqm = LQM()

    def to_dict(self):
        """Return JSON representation of the object."""

        return {'dpid': self.dpid,
                'port_id': self.port_id,
                'hwaddr': self.hwaddr,
                'iface': self.iface,
                'lqm': self.lqm}

    def __hash__(self):

        return hash(self.dpid) + hash(self.port_id)

    def __eq__(self, other):

        return other.dpid == self.dpid and other.port_id == self.port_id

    def __repr__(self):

        out = "%s port_id %u hwaddr %s iface %s" % (self.dpid,
                                                    self.port_id,
                                                    self.hwaddr,
                                                    self.iface)

        return out
