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

"""EmPOWER Radio Port."""

from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import BT_HT20


class RadioPort():
    """RadioPort class.

    A port represents the properties of an assignment LVAP <-> ResourceBlock.
    The PortProp class extends the dictornary overriding the set method in
    order to send a Port Update message when the port is changed and an ADD/
    DEL LVAP when a port is added/removed.

    Attributes:

      lvap, an LVAP object
      block, the block that this port is configuring
    """

    def __init__(self, lvap, block):

        self._lvap = lvap
        self._block = block

        txp = self._block.tx_policies[self._lvap.addr]

        if self._block.channel > 14:
            txp._mcs = [6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48.0, 54.0]
        else:
            txp._mcs = [1.0, 2.0, 5.5, 11.0,
                        6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48, 54.0]

        if self._lvap.supported_band == BT_HT20:
            txp._ht_mcs = \
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        else:
            txp._ht_mcs = []

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Port """

        return {'no_ack': self.no_ack,
                'mcs': self.mcs,
                'ht_mcs': self.ht_mcs,
                'rts_cts': self.rts_cts}

    @property
    def tx_policy(self):
        """ Return the TX policy. """

        return self._block.tx_policies[self._lvap.addr]

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
        """ Set the block. """

        self._block = block

    @property
    def mcs(self):
        """ Get set of MCS. """

        return self._block.tx_policies[self._lvap.addr].mcs

    @mcs.setter
    def mcs(self, mcs):
        """ Set the list of MCS. """

        self._block.tx_policies[self._lvap.addr].mcs = mcs

    @property
    def ht_mcs(self):
        """ Get set of HT MCS. """

        return self._block.tx_policies[self._lvap.addr].ht_mcs

    @ht_mcs.setter
    def ht_mcs(self, ht_mcs):
        """ Set the list of HT MCS. """

        self._block.tx_policies[self._lvap.addr].ht_mcs = ht_mcs

    @property
    def no_ack(self):
        """ Get no ack flag. """

        return self._block.tx_policies[self._lvap.addr].no_ack

    @no_ack.setter
    def no_ack(self, no_ack):
        """ Set the no ack flag. """

        self._block.tx_policies[self._lvap.addr].no_ack = no_ack

    @property
    def rts_cts(self):
        """ Get rts_cts . """

        return self._block.tx_policies[self._lvap.addr].rts_cts

    @rts_cts .setter
    def rts_cts(self, rts_cts):
        """ Set rts_cts . """

        self._block.tx_policies[self._lvap.addr].rts_cts = rts_cts

    def __eq__(self, other):

        return other.lvap == self.lvap

    def __repr__(self):

        no_ack = self.no_ack
        mcs = ', '.join([str(x) for x in sorted(list(self.mcs))])

        out = "(%s, mcs [%s], rts/cts %u, ack %s)" % \
            (self.lvap.addr, mcs, self.rts_cts, str(no_ack))

        return out


class RadioPortProp(dict):
    """PortProp class."""

    MAX_PORTS = 1
    SET_MASK = True

    def delitem(self, key):
        """Notice this will del the item without sending out any message."""

        if not isinstance(key, ResourceBlock):
            raise KeyError("Expected ResourceBlock, got %s" % type(key))

        dict.__delitem__(self, key)

    def __delitem__(self, key):

        if not isinstance(key, ResourceBlock):
            raise KeyError("Expected ResourceBlock, got %s" % type(key))

        # get port
        port = dict.__getitem__(self, key)

        # send del lvap message (key.radio is an WTP object, while port.lvap
        # is an LVAP object)
        stream = key.radio.connection.stream
        if stream and not stream.closed():
            key.radio.connection.send_del_lvap(port.lvap)

        dict.__delitem__(self, key)

    def setitem(self, key, value):
        """Notice this will set the item without sending out any message."""

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

            # update LVAP configuration
            key.radio.connection.send_add_lvap(value.lvap, key, self.SET_MASK)

            # update Port configuration
            key.radio.connection.send_set_port(value.tx_policy)

    def __getitem__(self, key):

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
