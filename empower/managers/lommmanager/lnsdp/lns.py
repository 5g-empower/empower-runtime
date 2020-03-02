#!/usr/bin/env python3
#
# Copyright (c) 2020 Fondazione Bruno Kessler
# Author(s): Cristina Costa (ccosta@fbk.eu)
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

from empower.managers.lommmanager.datatypes.eui64     import EUI64Field
from empower.managers.lommmanager.datatypes.websocket import WSURIField

P_STATE_ACTIVE      = "active"
P_STATE_SUSPENDED   = "suspended"


class LNS(MongoModel):
    """LNS class.

    The Device State machine is the following:

    active <-> suspended
    
    Attributes:
        euid: This LNS EUID
        ip:   This LNS IP address (IPAddress)
        port: This LNS port
        desc: A human-radable description of this Device (str)
        log:  logging facility
    """
    euid     = EUI64Field(primary_key=True) # 64 bit gateway identifier, EUI-64
    uri      = WSURIField(required=True)
    lgtws    = fields.ListField(default=[], blank=True, required=False)
    desc     = fields.CharField(required=True)


    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # self.__connection = None
        self.last_seen = 0
        self.last_seen_ts = 0
        self.period = 0
        # self.__state = P_STATE_SUSPENDED
        self.log = logging.getLogger("%s" % self.__class__.__module__)
        
        return None

    # @property
    # def state(self):
    #     """Return the state."""

    #     return self.__state

    # @state.setter
    # def state(self, state):
    #     """Set the Device state."""

    #     self.log.info("Device %s mode %s->%s", self.euid, self.state, state)

    #     method = "_%s_%s" % (self.state, state)

    #     if hasattr(self, method):
    #         callback = getattr(self, method)
    #         callback()
    #         return

    #     raise IOError("Invalid transistion %s -> %s" % (self.state, state))

    # def set_connected(self):
    #     """Move to connected state."""

    #     self.state = P_STATE_CONNECTED

    # def is_connected(self):
    #     """Return true if the device is connected"""

    #     return self.state == P_STATE_CONNECTED or self.is_online()

    # def set_disconnected(self):
    #     """Move to connected state."""

    #     self.state = P_STATE_DISCONNECTED

    # def set_online(self):
    #     """Move to connected state."""

    #     self.state = P_STATE_ONLINE

    # def is_online(self):
    #     """Return true if the device is online"""

    #     return self.state == P_STATE_ONLINE

    # def _online_online(self):

    #     # null transition
    #     pass

    # def _disconnected_connected(self):

    #     # set new state
    #     self.__state = P_STATE_CONNECTED

    # def _connected_disconnected(self):

    #     # set new state
    #     self.__state = P_STATE_DISCONNECTED

    # def _online_disconnected(self):

    #     # generate bye message
    #     self.__connection.send_device_down_message_to_self()

    #     # set new state
    #     self.__state = P_STATE_DISCONNECTED

    # def _connected_online(self):

    #     # set new state
    #     self.__state = P_STATE_ONLINE

    #     # generate register message
    #     self.__connection.send_device_up_message_to_self()

    # @property
    # def connection(self):
    #     """Get the connection assigned to this Device."""

    #     return self.__connection

    # @connection.setter
    # def connection(self, connection):
    #     """Set the connection assigned to this Device."""

    #     self.__connection = connection

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        date = datetime.fromtimestamp(self.last_seen_ts) \
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        out = {
            'euid': self.euid,
            'desc': self.desc,
            'uri': self.uri,
            'lgtws':self.lgtws,
            'last_seen': self.last_seen,
            'last_seen_ts': date,
            'period': self.period,
            # 'state': self.state
        }

        # out['connection'] = \
        #     self.connection.to_dict() if self.connection else None

        return out

    def to_str(self):
        """Return an ASCII representation of the object."""

        # if self.connection:
        #     return "%s at %s last_seen %d" % (self.euid,
        #                                       self.connection.to_str(),
        #                                       self.last_seen)

        return "%s" % self.euid

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.euid)

    def __eq__(self, other):
        if isinstance(other, LNS):
            return self.euid == other.euid
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
