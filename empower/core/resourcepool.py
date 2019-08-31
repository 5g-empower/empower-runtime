#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

BT_L20 = 0
BT_HT20 = 1

L20 = 'L20'
HT20 = 'HT20'

BANDS = {BT_L20: L20,
         BT_HT20: HT20}

REVERSE_BANDS = {L20: BT_L20,
                 HT20: BT_HT20}


class ResourcePool(list):
    """Resource pool.

    This extends the list in order to add a few filtering and sorting methods
    """

    def sort_by_rssi(self, addr):
        """Return list sorted by rssi for the specific address."""

        filtered = [x for x in self if addr in x.ucqm]

        blocks = sorted(filtered,
                        key=lambda x: x.ucqm[addr]['mov_rssi'],
                        reverse=True)

        return ResourcePool(blocks)

    def filter_by_channel(self, channel):
        """Return list sorted filtered by channel."""

        blocks = []

        for block in self.__iter__():
            if block.channel == channel:
                blocks.append(block)

        return ResourcePool(blocks)

    def filter_by_band(self, band):
        """Return list sorted filtered by band."""

        blocks = []

        for block in self.__iter__():
            if block.band == band:
                blocks.append(block)

        return ResourcePool(blocks)

    def first(self):
        """Return first entry in the list."""

        if self:
            block = list.__getitem__(self, 0)
            return ResourcePool([block])

        return ResourcePool()

    def last(self):
        """Return last entry in the list."""

        if self:
            block = list.__getitem__(self, -1)
            return ResourcePool([block])

        return ResourcePool()


class ResourceBlock:
    """A Wi-Fi AP interface.

    Attributes:
        wtp: The WTP at which this resource block is available
        block_id: the numeric interace identifier
        hwaddr: the mac address of the wireless interface
        channel: The channel number
        band: The band type (0=L20, 1=HT20)
        tx_policies: the tx policies active on this interface
        supports/ht_supports: list of MCS supported in this Resource Block as
          reported by the device, that is if the device is an 11a
          device it will report [6, 12, 18, 36, 54]. If the device is
          an 11n device it will report [0, 1, 2, 3, 4, 5, 6, 7]
        ucqm: User channel quality map.
        ncqm: Network channel quality map.
        channel_stats: Wi-Fi channel statistics (ED, TX, RX, ID)
        slice_stats: slice statistics
    """

    def __init__(self, wtp, block_id, hwaddr, channel, band):

        # Block properties (Immutable)
        self._block_id = block_id
        self._wtp = wtp
        self._hwaddr = hwaddr
        self._channel = channel
        self._band = band

        # Supported MCS
        self._supports = set()
        self._ht_supports = set()

        # TX Policies
        self.tx_policies = dict()

        # Statistics
        self.ucqm = {}
        self.ncqm = {}
        self.channel_stats = {}
        self.slice_stats = {}

        if self.channel > 14:
            self.supports = [6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48.0, 54.0]
        else:
            self.supports = [1.0, 2.0, 5.5, 11.0,
                             6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48, 54.0]

        if self.band == BT_HT20:
            self.ht_supports = [0, 1, 2, 3, 4, 5, 6, 7,
                                8, 9, 10, 11, 12, 13, 14, 15]

    @property
    def block_id(self):
        """Return the block_id."""

        return self._block_id

    @block_id.setter
    def block_id(self, block_id):
        """Set the block_id."""

        self._block_id = block_id

    @property
    def wtp(self):
        """Return the wtp."""

        return self._wtp

    @wtp.setter
    def wtp(self, wtp):
        """Set the wtp."""

        self._wtp = wtp

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
        """Return JSON-serializable representation of the object."""

        return {'addr': self.wtp.addr,
                'hwaddr': self.hwaddr,
                'channel': self.channel,
                'supports': sorted(self.supports),
                'ht_supports': sorted(self.ht_supports),
                'tx_policies': self.tx_policies,
                'band': BANDS[self.band]}

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "wtp %s hwaddr %s channel %s band %s" % \
            (self.wtp.addr, self.hwaddr, self.channel, BANDS[self.band])

    def __hash__(self):

        return hash(self.wtp.addr) + hash(self.hwaddr) + \
            hash(self.channel) + hash(self.band)

    def __eq__(self, other):

        if not isinstance(other, ResourceBlock):
            return False

        return (other.wtp == self.wtp and
                other.hwaddr == self.hwaddr and
                other.channel == self.channel and
                other.band == self.band)

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
