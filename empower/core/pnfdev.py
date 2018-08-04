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

"""EmPOWER Programmable Network Fabric Device Class."""

from datetime import datetime

import empower.logger

P_STATE_DISCONNECTED = "disconnected"
P_STATE_CONNECTED = "connected"
P_STATE_ONLINE = "online"


class BasePNFDev:
    """A Programmable Network Fabric Device (PNFDev).

    The PNFDev State machine is the following:

    disconnected <-> connected -> online
    online -> disconnected

    Attributes:
        addr: This PNFDev MAC address (EtherAddress)
        label: A human-radable description of this PNFDev (str)
        connection: Signalling channel connection (BasePNFPMainHandler)
        last_seen: Sequence number of the last hello message received (int)
        last_seen_ts: Timestamp of the last hello message received (int)
        seq: Next sequence number (int)
        period: update period (in ms)
        datapath: the associated OF switch
        state: this device status
        log: logging facility
    """

    ALIAS = "pnfdevs"

    def __init__(self, addr, label):

        self.addr = addr
        self.label = label
        self.__connection = None
        self.last_seen = 0
        self.last_seen_ts = 0
        self.__seq = 0
        self.period = 0
        self.datapath = None
        self.__state = P_STATE_DISCONNECTED
        self.log = empower.logger.get_logger()

    @property
    def state(self):
        """Return the state."""

        return self.__state

    @state.setter
    def state(self, state):
        """Set the PNFDev state."""

        self.log.info("PNFDev %s mode %s->%s", self.addr, self.state, state)

        method = "_%s_%s" % (self.state, state)

        if hasattr(self, method):
            callback = getattr(self, method)
            callback()
            return

        raise IOError("Invalid transistion %s -> %s" % (self.state, state))

    def set_connected(self):
        """Move to connected state."""

        self.state = P_STATE_CONNECTED

    def is_connected(self):
        """Return if pnfdev is connected"""

        return self.state == P_STATE_CONNECTED or self.is_online()

    def set_disconnected(self):
        """Move to connected state."""

        self.state = P_STATE_DISCONNECTED

    def set_online(self):
        """Move to connected state."""

        self.state = P_STATE_ONLINE

    def is_online(self):
        """Return if pnfdev is online"""

        return self.state == P_STATE_ONLINE

    def _online_online(self):

        # null transition
        pass

    def _disconnected_connected(self):

        # set new state
        self.__state = P_STATE_CONNECTED

    def _connected_disconnected(self):

        # set new state
        self.__state = P_STATE_DISCONNECTED

    def _online_disconnected(self):

        # generate bye message
        self.__connection.send_bye_message_to_self()

        # set new state
        self.__state = P_STATE_DISCONNECTED

    def _connected_online(self):

        # set new state
        self.__state = P_STATE_ONLINE

        # generate register message
        self.__connection.send_register_message_to_self()

    @property
    def connection(self):
        """Get the connection assigned to this PNFDev."""

        return self.__connection

    @connection.setter
    def connection(self, connection):
        """Set the connection assigned to this PNFDev."""

        self.__connection = connection

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the PNFDev."""

        date = datetime.fromtimestamp(self.last_seen_ts) \
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        return {'addr': self.addr,
                'last_seen': self.last_seen,
                'last_seen_ts': date,
                'period': self.period,
                'label': self.label,
                'datapath': self.datapath,
                'state': self.state,
                'connection': self.connection}

    @property
    def seq(self):
        """Return new sequence id."""

        self.__seq += 1
        return self.__seq

    def __str__(self):

        if self.connection:
            return "%s at %s last_seen %d" % (self.addr,
                                              self.connection.addr[0],
                                              self.last_seen)

        return "%s" % (self.addr)

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, BasePNFDev):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
