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

"""EmPOWER Radio Port."""

from empower.core.resourcepool import build_block
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool

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


class RadioPort():
    """RadioPort class.

    A port represents the properties of an assignment LVAP <-> ResourceBlock.
    The PortProp class extends the dictornary overriding the set method in
    order to send a Port Update message when the port is changed and an ADD/
    DEL LVAP when a port is added/removed. Examples:

      lvap.block = block

    pool is a ResourcePool object. This results effectivelly in:

      for block in pool:
        lvap.block[block] = Port(lvap, block)

    Similarly:

      lvap.block[block] = port

    is used to update a port configuration

    Attributes:

      lvap, an LVAP object
      block, the block that this port is configuring
      no_ack, do not wait for ACKs when transmitting to this LVAP
      rts_cts, use RTS/CTS when transmitting to this LVAP
      mcs, supported mcs-es.
    """

    def __init__(self, lvap, block):

        self._lvap = lvap
        self._block = block
        self._no_ack = False
        self._rts_cts = 2346
        self._tx_mcast = TX_MCAST_LEGACY
        self._ur_mcast_count = 3

        match = (lvap.supports & ResourcePool([block])).pop()
        self._mcs = block.supports & match.supports

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Port """

        return {'no_ack': self.no_ack,
                'mcs': self.mcs,
                'rts_cts': self.rts_cts,
                'tx_mcast': TX_MCAST[self.tx_mcast],
                'ur_mcast_count': self._ur_mcast_count}

    @property
    def lvap(self):
        """ Return the lvap. """

        return self._lvap

    @lvap.setter
    def lvap(self, lvap):
        """ Set the LVAP. """

        self._lvap = lvap

    @property
    def block(self):
        """ Return the block. """

        return self._block

    @block.setter
    def block(self, block):
        """ Set the LVAP. """

        self._block = block

    @property
    def mcs(self):
        """ Get set of MCS. """

        return self._mcs

    @mcs.setter
    def mcs(self, mcs):
        """ Set the list of MCS. """

        self._mcs = self._block.supports & set(mcs)
        self.block.radio.connection.send_set_port(self)

    @property
    def no_ack(self):
        """ Get no ack flag. """

        return self._no_ack

    @no_ack.setter
    def no_ack(self, no_ack):
        """ Set no ack flag. """

        self._no_ack = True if no_ack else False
        self.block.radio.connection.send_set_port(self)

    @property
    def rts_cts(self):
        """ Get rts_cts flag. """

        return self._rts_cts

    @rts_cts.setter
    def rts_cts(self, rts_cts):
        """ Set rts_cts flag. """

        self._rts_cts = rts_cts
        self.block.radio.connection.send_set_port(self)

    @property
    def tx_mcast(self):
        """ Get tx_mcast. """

        return self._tx_mcast

    @tx_mcast.setter
    def tx_mcast(self, tx_mcast):
        """ Set tx_mcast. """

        if tx_mcast not in TX_MCAST:
            raise ValueError("Invalid tx mast %s" % tx_mcast)

        self._tx_mcast = tx_mcast
        self.block.radio.connection.send_set_port(self)

    @property
    def ur_mcast_count(self):
        """ Get ur_mcast_count. """

        return self._ur_mcast_count

    @ur_mcast_count.setter
    def ur_mcast_count(self, ur_mcast_count):
        """ Set tx_mcast. """

        self._ur_mcast_count = 5#int(ur_mcast_count)
        self.block.radio.connection.send_set_port(self)

    def __eq__(self, other):

        return other.lvap == self.lvap

    def __repr__(self):

        no_ack = self.no_ack
        mcs = ', '.join([str(x) for x in sorted(list(self.mcs))])
        tx_mcast = TX_MCAST[self.tx_mcast]
        ur_mcast_count = self._ur_mcast_count

        out = "(%s, mcs [%s], rts/cts %u, ack %s, mcast %s, ur %u)" % \
            (self.lvap.addr, mcs, self.rts_cts, str(no_ack), tx_mcast,
             ur_mcast_count)

        return out


class RadioPortProp(dict):
    """PortProp class."""

    MAX_PORTS = 1
    SET_MASK = True

    def delitem(self, key):
        """Notice this will del the item without sending out any message."""

        key = build_block(key)

        if not isinstance(key, ResourceBlock):
            raise KeyError("Expected ResourceBlock, got %s" % type(key))

        dict.__delitem__(self, key)

    def __delitem__(self, key):

        key = build_block(key)

        if not isinstance(key, ResourceBlock):
            raise KeyError("Expected ResourceBlock, got %s" % type(key))

        # get port
        port = dict.__getitem__(self, key)

        # send del lvap message (key.radio is an WTP object, while port.lvap
        # is an LVAP object)
        key.radio.connection.send_del_lvap(port.lvap)

        dict.__delitem__(self, key)

    def setitem(self, key, value):
        """Notice this will set the item without sending out any message."""

        key = build_block(key)

        if not isinstance(key, ResourceBlock):
            raise KeyError("Expected ResourceBlock, got %s" % type(key))

        if not isinstance(value, RadioPort):
            raise KeyError("Expected Port, got %s" % type(key))

        # the block is found, update the port
        if dict.__contains__(self, key):

            # update dict
            dict.__setitem__(self, key, value)

        # the block is not found, max_ports is exceed
        elif dict.__len__(self) == self.MAX_PORTS:

            raise ValueError("Max number of ports is %u" % self.MAX_PORTS)

        # the block is not found, max_ports is not exceed
        else:

            # update dict
            dict.__setitem__(self, key, value)

    def __setitem__(self, key, value):

        key = build_block(key)

        if not isinstance(key, ResourceBlock):
            raise KeyError("Expected ResourceBlock, got %s" % type(key))

        if not isinstance(value, RadioPort):
            raise KeyError("Expected Port, got %s" % type(key))

        # the block is found, update the port
        if dict.__contains__(self, key):

            # update dict
            dict.__setitem__(self, key, value)

            # update port configuration
            key.radio.connection.send_set_port(value)

        # the block is not found, max_ports is exceed
        elif dict.__len__(self) == self.MAX_PORTS:

            raise ValueError("Max number of ports is %u" % self.MAX_PORTS)

        # the block is not found, max_ports is not exceed
        else:

            # update dict
            dict.__setitem__(self, key, value)

            # update LVAP configuration
            key.radio.connection.send_add_lvap(value.lvap, key, self.SET_MASK)

            # update Port configuration
            key.radio.connection.send_set_port(value)

    def __getitem__(self, key):

        key = build_block(key)

        if not isinstance(key, ResourceBlock):
            raise KeyError("Expected ResourceBlock, got %s" % type(key))

        return dict.__getitem__(self, key)


class DownlinkPort(RadioPortProp):
    """Downlink PortProp class."""

    MAX_PORTS = 1
    SET_MASK = True


class UplinkPort(RadioPortProp):
    """Uplink PortProp class."""

    MAX_PORTS = 10
    SET_MASK = False
