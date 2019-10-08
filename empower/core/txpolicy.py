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

"""Transmission policy."""

import logging

from empower.core.resourcepool import BT_HT20

TX_AMSDU_LEN_4K = 3839
TX_AMSDU_LEN_8K = 7935

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
        max_amsdu_len: the maximum aggregation size in bytes
        mcast: the multicast mode (DMS, LEGACY, UR)
        mcs: the list of legacy MCSes
        ht_mcs: the list of HT MCSes
    """

    def __init__(self, addr, block):

        self.addr = addr
        self.block = block
        self._no_ack = False
        self._rts_cts = 2436
        self._max_amsdu_len = TX_AMSDU_LEN_4K
        self._mcast = TX_MCAST_LEGACY
        self._mcs = block.supports
        self._ht_mcs = block.ht_supports
        self._ur_count = 3

        # logger :)
        self.log = logging.getLogger(self.__class__.__module__)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = {
            'addr': self.addr,
            'no_ack': self.no_ack,
            'rts_cts': self.rts_cts,
            'max_amsdu_len': self._max_amsdu_len,
            'mcast': TX_MCAST[self.mcast],
            'mcs': sorted(self.mcs),
            'ht_mcs': sorted(self.ht_mcs),
            'ur_count': self.ur_count
        }

        return out

    @property
    def ur_count(self):
        """Get ur_count."""

        return self._ur_count

    @ur_count .setter
    def ur_count(self, ur_count):
        """Set ur_count."""

        self.set_ur_count(ur_count)

        self.block.wtp.connection.send_set_tx_policy(self)

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

        self.block.wtp.connection.send_set_tx_policy(self)

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

        self.block.wtp.connection.send_set_tx_policy(self)

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

        self.block.wtp.connection.send_set_tx_policy(self)

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

        self.block.wtp.connection.send_set_tx_policy(self)

    def set_no_ack(self, no_ack):
        """Set the no ack flag without sending anything."""

        self._no_ack = bool(no_ack)

    @property
    def rts_cts(self):
        """Get rts_cts."""

        return self._rts_cts

    @rts_cts.setter
    def rts_cts(self, rts_cts):
        """Set rts_cts."""

        self.set_rts_cts(rts_cts)

        self.block.wtp.connection.send_set_tx_policy(self)

    def set_rts_cts(self, rts_cts):
        """Set rts_cts without sending anything."""

        self._rts_cts = int(rts_cts)

    @property
    def max_amsdu_len(self):
        """Get max_amsdu_len."""

        return self._max_amsdu_len

    @max_amsdu_len.setter
    def max_amsdu_len(self, max_amsdu_len):
        """Set max_amsdu_len."""

        self.set_max_amsdu_len(max_amsdu_len)

        self.block.wtp.connection.send_set_tx_policy(self)

    def set_max_amsdu_len(self, max_amsdu_len):
        """Set max_amsdu_len without sending anything."""

        self._max_amsdu_len = int(max_amsdu_len)

    def __hash__(self):

        return hash(self.addr) + hash(self.block)

    def __eq__(self, other):

        if not isinstance(other, TxPolicy):
            return False

        return (other.addr == self.addr and
                other.block == self.block and
                other.no_ack == self.no_ack and
                other.rts_cts == self.rts_cts and
                other.max_amsdu_len == self.max_amsdu_len and
                other.mcast == self.mcast and
                other.mcs == self.mcs and
                other.ht_mcs == self.ht_mcs)

    def to_str(self):
        """Return an ASCII representation of the object."""

        mcs = ", ".join([str(x) for x in self.mcs])
        ht_mcs = ", ".join([str(x) for x in self.ht_mcs])

        if self.block.band == BT_HT20:
            state = \
                "%s no_ack %s rts_cts %u max_amsdu %u mcast %s ur_count %u " \
                "ht_mcs %s" % \
                (self.addr, self.no_ack, self.rts_cts, self.max_amsdu_len,
                 TX_MCAST[self.mcast], self.ur_count, ht_mcs)
        else:
            state = \
                "%s no_ack %s rts_cts %u max_amsdu %u mcast %s ur_count %u " \
                "mcs %s" % \
                (self.addr, self.no_ack, self.rts_cts, self.max_amsdu_len,
                 TX_MCAST[self.mcast], self.ur_count, mcs)

        return state

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
