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

"""EmPOWER transmission policy class."""

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


class TxPolicy:
    """Transmission policy.

    A transmission policy is a set of rule that must be used by the rate
    control algorithm to select the actual transmission rate.

    Attributes:
        block: the actual block to which this tx policy refers to
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
                'mcs': sorted(self.mcs),
                'ht_mcs': sorted(self.ht_mcs),
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

        self._ht_mcs = self.block.ht_supports & set(ht_mcs)

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
