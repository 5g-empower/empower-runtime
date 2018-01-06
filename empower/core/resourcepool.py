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

"""EmPOWER resouce pool and resource block classes."""

from empower.datatypes.etheraddress import EtherAddress
from empower.core.transmissionpolicy import TxPolicy
from empower.core.trafficrule import TrafficRule

BT_L20 = 0
BT_HT20 = 1

L20 = 'L20'
HT20 = 'HT20'

BANDS = {BT_L20: L20,
         BT_HT20: HT20}

REVERSE_BANDS = {L20: BT_L20,
                 HT20: BT_HT20}


class TxPolicyProp(dict):
    """Override getitem behaviour by a default TxPolicy."""

    def __init__(self, block, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.block = block

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            value = TxPolicy(key, self.block)
            dict.__setitem__(self, key, value)
            return dict.__getitem__(self, key)


class TrafficRuleQueueProp(dict):
    """Override getitem behaviour by a default TxRule."""

    def __init__(self, block, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.block = block

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            value = TrafficRule(ssid=key[0], dscp=key[1], block=self.block)
            dict.__setitem__(self, key, value)
            return dict.__getitem__(self, key)


class CQM(dict):
    """Override getitem behaviour by returning -inf instead of KeyError
    when the key is missing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):

        try:

            return dict.__getitem__(self, key)

        except KeyError:

            inf = {'addr': key,
                   'last_rssi_std': -float("inf"),
                   'last_rssi_avg': -float("inf"),
                   'last_packets': 0,
                   'hist_packets': 0,
                   'mov_rssi': -float("inf")}

            return inf


class ResourcePool(list):
    """ EmPOWER resource pool.

    This extends the list in order to add a few filtering and sorting methods
    """

    def sortByRssi(self, addr):
        blocks = sorted(self, key=lambda x: x.ucqm[addr]['mov_rssi'],
                        reverse=True)
        return ResourcePool(blocks)

    def first(self):
        block = list.__getitem__(self, 0)
        return ResourcePool([block])

    def last(self):
        selected = list.__getitem__(self, -1)
        return ResourcePool([block])


class ResourceBlock:
    """ EmPOWER resource block.

    A resource block is identified by a channel, a timeslot, and the
    spatial stream id. Channel is a tuple in the form (channel number, channel
    type).  Channel type is one of the channel supported by 802.11: 20, 20HT,
    40HT, 40VHT, 80VHT.

    Attributes:
        radio: The WTP or the LVAP at which this resource block is available
        hwaddr: the mac address of the wireless interface
        channel: The channel id
        band: The band type (0=L20, 1=HT20)
        ucqm: User interference matrix group. Rssi values to LVAPs.
        ncqm: Network interference matrix group. Rssi values to WTPs.
        supports: list of MCS supported in this Resource Block as
          reported by the device, that is if the device is an 11a
          device it will report [6, 12, 18, 36, 54]. If the device is
          an 11n device it will report [0, 1, 2, 3, 4, 5, 6, 7]
    """

    def __init__(self, radio, hwaddr, channel, band):

        self._radio = radio
        self._hwaddr = hwaddr
        self._channel = channel
        self._band = band
        self.ucqm = CQM()
        self.ncqm = CQM()
        self.wifi_stats = {}
        self.tx_policies = TxPolicyProp(self)
        self.traffic_rules = TrafficRuleQueueProp(self)
        self._supports = set()
        self._ht_supports = set()

        if self.channel > 14:
            self.supports = [6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48.0, 54.0]
        else:
            self.supports = [1.0, 2.0, 5.5, 11.0,
                             6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48, 54.0]

        if self.band == BT_HT20:
            self.ht_supports = [0, 1, 2, 3, 4, 5, 6, 7,
                                8, 9, 10, 11, 12, 13, 14, 15]

    @property
    def addr(self):
        """ Return the radio's address. """

        return self._radio.addr

    @property
    def radio(self):
        """ Return the radio. """

        return self._radio

    @radio.setter
    def radio(self, radio):
        """ Set the band. """

        self._radio = radio

    @property
    def supports(self):
        """ Return the list of supported MCS. """

        return self._supports

    @supports.setter
    def supports(self, supports):
        """ Set the list of supported. """

        for supported in supports:
            self._supports.add(int(supported))

    @property
    def ht_supports(self):
        """ Return the list of supported MCS (HT). """

        return self._ht_supports

    @ht_supports.setter
    def ht_supports(self, ht_supports):
        """ Set the list of supported MCS (HT). """

        for supported in ht_supports:
            self._ht_supports.add(int(supported))

    @property
    def hwaddr(self):
        """ Return the hwaddr. """

        return self._hwaddr

    @hwaddr.setter
    def hwaddr(self, hwaddr):
        """ Set the hwaddr. """

        self._hwaddr = hwaddr

    @property
    def band(self):
        """ Return the band. """

        return self._band

    @band.setter
    def band(self, band):
        """ Set the band. """

        if band not in BANDS:
            raise ValueError("Invalid band type %s" % band)

        self._band = band

    @property
    def channel(self):
        """ Return the channel. """

        return self._channel

    @channel.setter
    def channel(self, channel):
        """ Set the band. """

        if channel < 1 or channel > 165:
            raise ValueError("Invalid channel %u" % channel)

        self._channel = channel

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Resource
        Pool """

        tx_policies = {str(k): v for k, v in self.tx_policies.items()}
        traffic_rules = {"%s-%u" % k: v for k, v in self.traffic_rules.items()}

        return {'addr': self.radio.addr,
                'hwaddr': self.hwaddr,
                'channel': self.channel,
                'supports': sorted(self.supports),
                'ht_supports': sorted(self.ht_supports),
                'tx_policies': tx_policies,
                'band': BANDS[self.band],
                'traffic_rules': traffic_rules,
                'wifi_stats': self.wifi_stats,
                'ucqm': {str(k): v for k, v in self.ucqm.items()},
                'ncqm': {str(k): v for k, v in self.ncqm.items()}}

    def __hash__(self):

        return hash(self.radio.addr) + hash(self.hwaddr) + \
            hash(self.channel) + hash(self.band)

    def __eq__(self, other):

        if not isinstance(other, ResourceBlock):
            return False

        return (other.radio == self.radio and
                other.hwaddr == self.hwaddr and
                other.channel == self.channel and
                other.band == self.band)

    def __repr__(self):
        return "(%s, %s, %u, %s)" % (self.radio.addr, self.hwaddr,
                                     self.channel, BANDS[self.band])
