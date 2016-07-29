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


class BasePNFDev(object):
    """A Programmable Network Fabric Device (PNFDev).

    Attributes:
        addr: This PNFDev MAC address (EtherAddress)
        label: A human-radable description of this PNFDev (str)
        connection: Signalling channel connection (BasePNFPMainHandler)
        last_seen: Sequence number of the last hello message received (int)
        last_seen_ts: Timestamp of the last hello message received (int)
        feed: The power consumption monitoring feed (Feed)
        seq: Next sequence number (int)
        every: update period (in ms)
        uplink_bytes: signalling channel uplink bytes
        uplink_bit_rate: signalling channel uplink bit rate
        downlink_bytes: signalling channel downlink bytes
        downlink_bit_rate: signalling channel downlink bit rate
        ports: OVS ports
    """

    ALIAS = "pnfdevs"
    SOLO = "pnfdev"

    def __init__(self, addr, label):

        self.addr = addr
        self.label = label
        self.__connection = None
        self.last_seen = 0
        self.last_seen_ts = 0
        self.feed = None
        self.__seq = 0
        self.every = 0
        self.ports = {}

    @property
    def connection(self):
        """Get the connection assigned to this PNFDev."""

        return self.__connection

    @connection.setter
    def connection(self, connection):
        """Set the connection assigned to this PNFDev."""

        if not connection and self.__connection:
            self.__connection.send_bye_message_to_self()

        self.__connection = connection

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the PNFDev."""

        date = datetime.fromtimestamp(self.last_seen_ts) \
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        return {'addr': self.addr,
                'last_seen': self.last_seen,
                'last_seen_ts': date,
                'every': self.every,
                'label': self.label,
                'feed': self.feed,
                'ports': self.ports,
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
        else:
            return "%s" % (self.addr)

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, BasePNFDev):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def powerdown(self):
        """ Power down node. """

        if self.feed and self.feed.is_on:
            self.feed.is_on = False
            if self.connection:
                self.connection.stream.close()

    def powerup(self):
        """ Power up node. """

        if self.feed and not self.feed.is_on:
            self.feed.is_on = True
