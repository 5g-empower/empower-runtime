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
