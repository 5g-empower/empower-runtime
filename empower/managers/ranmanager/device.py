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

"""Base device class."""

import logging

from datetime import datetime
from pymodm import MongoModel, fields

from empower.core.etheraddress import EtherAddressField

P_STATE_DISCONNECTED = "disconnected"
P_STATE_CONNECTED = "connected"
P_STATE_ONLINE = "online"


class Device(MongoModel):
    """Base device class.

    The Device State machine is the following:

    disconnected <-> connected -> online
    online -> disconnected

    Attributes:
        addr: This Device MAC address (EtherAddress)
        desc: A human-radable description of this Device (str)
        connection: Signalling channel connection
        last_seen: Sequence number of the last hello message received (int)
        last_seen_ts: Timestamp of the last hello message received (int)
        period: update period (in ms)
        state: this device status
        log: logging facility
    """

    addr = EtherAddressField(primary_key=True)
    desc = fields.CharField(required=True)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.__connection = None
        self.last_seen = 0
        self.last_seen_ts = 0
        self.period = 0
        self.__state = P_STATE_DISCONNECTED
        self.log = logging.getLogger("%s" % self.__class__.__module__)

    @property
    def state(self):
        """Return the state."""

        return self.__state

    @state.setter
    def state(self, state):
        """Set the Device state."""

        self.log.info("Device %s mode %s->%s", self.addr, self.state, state)

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
        """Return true if the device is connected"""

        return self.state == P_STATE_CONNECTED or self.is_online()

    def set_disconnected(self):
        """Move to connected state."""

        self.state = P_STATE_DISCONNECTED

    def set_online(self):
        """Move to connected state."""

        self.state = P_STATE_ONLINE

    def is_online(self):
        """Return true if the device is online"""

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
        self.__connection.send_device_down_message_to_self()

        # set new state
        self.__state = P_STATE_DISCONNECTED

    def _connected_online(self):

        # set new state
        self.__state = P_STATE_ONLINE

        # generate register message
        self.__connection.send_device_up_message_to_self()

    @property
    def connection(self):
        """Get the connection assigned to this Device."""

        return self.__connection

    @connection.setter
    def connection(self, connection):
        """Set the connection assigned to this Device."""

        self.__connection = connection

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        date = datetime.fromtimestamp(self.last_seen_ts) \
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        out = {
            'addr': self.addr,
            'desc': self.desc,
            'last_seen': self.last_seen,
            'last_seen_ts': date,
            'period': self.period,
            'state': self.state
        }

        out['connection'] = \
            self.connection.to_dict() if self.connection else None

        return out

    def to_str(self):
        """Return an ASCII representation of the object."""

        if self.connection:
            return "%s at %s last_seen %d" % (self.addr,
                                              self.connection.to_str(),
                                              self.last_seen)

        return "%s" % self.addr

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
