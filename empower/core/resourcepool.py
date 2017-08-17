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

BT_L20 = 0
BT_HT20 = 1

L20 = 'L20'
HT20 = 'HT20'

BANDS = {BT_L20: L20,
         BT_HT20: HT20}

REVERSE_BANDS = {L20: BT_L20,
                 HT20: BT_HT20}

TX_MCAST_LEGACY = 0x0
TX_MCAST_DMS = 0x1
TX_MCAST_UR = 0x2

TX_MCAST_LEGACY_H = 'legacy'
TX_MCAST_DMS_H = 'dms'
TX_MCAST_UR_H = 'ur'

TX_MCAST = {TX_MCAST_LEGACY: TX_MCAST_LEGACY_H,
            TX_MCAST_DMS: TX_MCAST_DMS_H,
            TX_MCAST_UR: TX_MCAST_UR_H}

REVERSE_TX_MCAST = {TX_MCAST_LEGACY_H: TX_MCAST_LEGACY,
                    TX_MCAST_DMS_H: TX_MCAST_DMS,
                    TX_MCAST_UR_H: TX_MCAST_UR}


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


class TxPolicy(object):
    """Transmission policy.

    A transmission policy is a set of rule that must be used by the rate
    control algorithm to select the actual transmission rate.

    Attributes:
        block: the actuall block to which this tx policy refers to
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

    def __init__(self, addr, block):

        self.addr = addr
        self.block = block
        self._no_ack = False
        self._rts_cts = 2436
        self._mcast = TX_MCAST_LEGACY
        self._mcs = block.supports
        self._ht_mcs = block.ht_supports
        self._ur_count = 3

    def to_dict(self):
        """Return a json-frinedly representation of the object."""

        return {'no_ack': self.no_ack,
                'rts_cts': self.rts_cts,
                'mcast': TX_MCAST[self.mcast],
                'mcs': self.mcs,
                'ht_mcs': self.ht_mcs,
                'ur_count': self.ur_count}

    def __repr__(self):

        mcs = ", ".join([str(x) for x in self.mcs])
        ht_mcs = ", ".join([str(x) for x in self.ht_mcs])

        return \
            "%s no_ack %s rts_cts %u mcast %s mcs %s ht_mcs %s ur_count %u" % \
            (self.addr, self.no_ack, self.rts_cts, TX_MCAST[self.mcast],
             mcs, ht_mcs, self.ur_count)

    @property
    def ur_count(self):
        """ Get ur_count . """

        return self._ur_count

    @ur_count .setter
    def ur_count(self, ur_count):
        """ Set ur_count . """

        self._ur_count = int(ur_count)

        self.block.radio.connection.send_set_port(self)

    @property
    def mcast(self):
        """ Get mcast mode. """

        return self._mcast

    @mcast.setter
    def mcast(self, mcast):
        """ Set the mcast mode. """

        self._mcast = mcast if mcast in TX_MCAST else TX_MCAST_LEGACY

        self.block.radio.connection.send_set_port(self)

    @property
    def mcs(self):
        """ Get set of MCS. """

        return self._mcs

    @mcs.setter
    def mcs(self, mcs):
        """ Set the list of MCS. """

        self._mcs = self.block.supports & set(mcs)

        if not self._mcs:
            self._mcs = self.block.supports

        self.block.radio.connection.send_set_port(self)

    @property
    def ht_mcs(self):
        """ Get set of HT MCS. """

        return self._ht_mcs

    @ht_mcs.setter
    def ht_mcs(self, ht_mcs):
        """ Set the list of MCS. """

        self._ht_mcs = self.block.supports & set(ht_mcs)

        if not self._ht_mcs:
            self._ht_mcs = self.block.ht_supports

        self.block.radio.connection.send_set_port(self)

    @property
    def no_ack(self):
        """ Get no ack flag. """

        return self._no_ack

    @no_ack.setter
    def no_ack(self, no_ack):
        """ Set the no ack flag. """

        self._no_ack = True if no_ack else False

        self.block.radio.connection.send_set_port(self)

    @property
    def rts_cts(self):
        """ Get rts_cts . """

        return self._rts_cts

    @rts_cts.setter
    def rts_cts(self, rts_cts):
        """ Set rts_cts . """

        self._rts_cts = int(rts_cts)

        self.block.radio.connection.send_set_port(self)


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


class ResourceBlock(object):
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
        self.busyness = None
        self.tx_policies = TxPolicyProp(self)
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

        return {'addr': self.radio.addr,
                'hwaddr': self.hwaddr,
                'channel': self.channel,
                'supports': sorted(self.supports),
                'ht_supports': sorted(self.ht_supports),
                'tx_policies': tx_policies,
                'band': BANDS[self.band],
                'busyness': self.busyness,
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
