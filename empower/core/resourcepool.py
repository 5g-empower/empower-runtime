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

"""EmPOWER resouce pool and resource block classes."""

from empower.datatypes.etheraddress import EtherAddress

BT_L20 = 0
BT_HT20 = 1
BT_HT40 = 2

L20 = 'L20'
HT20 = 'HT20'
HT40 = 'HT40'

BANDS = {BT_L20: L20,
         BT_HT20: HT20,
         BT_HT40: HT40}

REVERSE_BANDS = {L20: BT_L20,
                 HT20: BT_HT20,
                 HT40: BT_HT40}

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
        band: The band type (0=L20, 1=HT20, 2=HT40)
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
        self._ur_count = 3

    def to_dict(self):
        """Return a json-frinedly representation of the object."""

        return {'no_ack': self.no_ack,
                'rts_cts': self.rts_cts,
                'mcast': TX_MCAST[self.mcast],
                'mcs': self.mcs,
                'ur_count': self.ur_count}

    def __repr__(self):

        mcs = ", ".join([str(x) for x in self.mcs])

        return "%s no_ack %s rts_cts %u mcast %s mcs %s ur_count %u" % \
            (self.addr, self.no_ack, self.rts_cts, TX_MCAST[self.mcast],
             mcs, self.ur_count)

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
                   'ewma_rssi': -float("inf"),
                   'sma_rssi': -float("inf")}

            return inf


def build_block(block):
    """Build a new resource block from another block or from a tuple."""

    if isinstance(block, ResourceBlock):

        requested = block

    elif isinstance(block, tuple):

        if len(tuple) < 3:
            raise ValueError("Invalid tuple")

        from empower.main import RUNTIME

        wtp = RUNTIME.wtps[EtherAddress(block[0])]
        hwaddr = EtherAddress(block[1])
        channel = block[2]
        band = REVERSE_BANDS[block[3]]
        requested = ResourceBlock(wtp, hwaddr, channel, band)

    else:

        raise ValueError("Expected ResourceBlock or tuple, got %s",
                         type(block))

    for supported in requested.radio.supports:
        if supported == requested:
            return supported

    raise KeyError(requested)


class ResourcePool(set):
    """ Resource Pool class.

    A resource block represents the minimum allocation element in a EmPOWER
    network. It typically consists of a wifi channel and the number of
    streams. However it could also consist of multiple bands (for example 160
    MHz channel obtained by aggregating two 80 MHz channels in 802.11ac
    networks).

    The class Overrides the set object's "and" method for ResourceBlock
    objects by excluding the Resource Block address form the matching.from
    """

    def __init__(self, *args, **kwds):
        super(ResourcePool, self).__init__(*args, **kwds)

    def __and__(self, other):
        result = ResourcePool()
        for rblock in self:
            for rblock_other in other:
                if rblock.channel == rblock_other.channel and \
                   rblock.band == rblock_other.band:

                    result.add(rblock)

        return result

    def __or__(self, other):
        result = ResourcePool()
        for rblock in self:
            result.add(rblock)
        for rblock in other:
            result.add(rblock)
        return result


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
        band: The band type (0=L20, 1=HT20, 2=HT40)
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
        self.tx_policies = TxPolicyProp(self)

        if self.band == BT_HT20 or self.band == BT_HT40:
            self._supports = set([0, 1, 2, 3, 4, 5, 6, 7])
        else:
            if self.channel > 14:
                self._supports = \
                    set([6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48.0, 54.0])
            else:
                self._supports = \
                    set([1.0, 2.0, 5.5, 11.0,
                         6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48, 54.0])

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
        """ Set the band. """

        for supported in supports:
            self._supports.add(int(supported))

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
                'tx_policies': tx_policies,
                'band': BANDS[self.band],
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
