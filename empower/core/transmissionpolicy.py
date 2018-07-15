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
        addr: the destination address to which this policy applies
        block: the actual block to which this tx policy refers to
        no_ack: do not wait for acks
        rts_cts: the rts/cts threshold in bytes
        mcast: the multicast mode (DMS, LEGACY, UR)
        mcs: the list of legacy MCSes
        ht_mcs: the list of HT MCSes
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
        """Get ur_count."""

        return self._ur_count

    @ur_count .setter
    def ur_count(self, ur_count):
        """Set ur_count."""

        self.set_ur_count(ur_count)

        self.block.radio.connection.send_set_transmission_policy(self)

    def set_ur_count(self, ur_count):
        """Set ur_count without sending anything."""

        self._ur_count = int(ur_count)

    @property
    def mcast(self):
        """Get mcast mode."""

        return self._mcast

    @mcast.setter
    def mcast(self, mcast):
        """Set the mcast mode."""

        self.set_mcast(mcast)

        self.block.radio.connection.send_set_transmission_policy(self)

    def set_mcast(self, mcast):
        """Set the mcast mode without sending anything."""

        self._mcast = int(mcast) if int(mcast) in TX_MCAST else TX_MCAST_LEGACY

    @property
    def mcs(self):
        """Get set of MCS."""

        return self._mcs

    @mcs.setter
    def mcs(self, mcs):
        """Set the list of MCS."""

        self.set_mcs(mcs)

        self.block.radio.connection.send_set_transmission_policy(self)

    def set_mcs(self, mcs):
        """Set the list of MCS without sending anything."""

        self._mcs = self.block.supports & set(mcs)

        if not self._mcs:
            self._mcs = self.block.supports

    @property
    def ht_mcs(self):
        """Get set of HT MCS."""

        return self._ht_mcs

    @ht_mcs.setter
    def ht_mcs(self, ht_mcs):
        """Set the list of MCS."""

        self.set_ht_mcs(ht_mcs)

        self.block.radio.connection.send_set_transmission_policy(self)

    def set_ht_mcs(self, ht_mcs):
        """Set the list of HT MCS without sending anything."""

        self._ht_mcs = self.block.ht_supports & set(ht_mcs)

        if not self._ht_mcs:
            self._ht_mcs = self.block.ht_supports

    @property
    def no_ack(self):
        """Get no ack flag."""

        return self._no_ack

    @no_ack.setter
    def no_ack(self, no_ack):
        """Set the no ack flag."""

        self.set_no_ack(no_ack)

        self.block.radio.connection.send_set_transmission_policy(self)

    def set_no_ack(self, no_ack):
        """Set the no ack flag without sending anything."""

        self._no_ack = True if bool(no_ack) else False

    @property
    def rts_cts(self):
        """Get rts_cts."""

        return self._rts_cts

    @rts_cts.setter
    def rts_cts(self, rts_cts):
        """Set rts_cts."""

        self.set_rts_cts(rts_cts)

        self.block.radio.connection.send_set_transmission_policy(self)

    def set_rts_cts(self, rts_cts):
        """Set rts_cts without sending anything."""

        self._rts_cts = int(rts_cts)
