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
"""EmPOWER Runtime LoRaWAN Gateway Class."""

import logging

from datetime import datetime
from enum import Enum, unique
from pymodm import MongoModel, fields

# from empower.core.eui64 import EUI64
from empower.core.eui64 import EUI64Field
from empower.managers.lommmanager.lnsp import DEFAULT_OWNER


@unique
class LGtwState(Enum):
    """Enumerate lGTW states."""

    # TODO Full test of lGtw State Machine

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ONLINE = "online"
    RMTSH = "remote shell"  # Remote Shell mode on

    @property
    def next_valid(self):
        """Return the next valid state for lgtw.

        The lgtw state machine is the following:
            disconnected <-> connected -> online
            online <-> rmsh
            online -> disconnected
        """
        if self == LGtwState.DISCONNECTED:
            return [self, LGtwState.CONNECTED]
        if self == LGtwState.CONNECTED:
            return [self, LGtwState.DISCONNECTED, LGtwState.ONLINE]
        if self == LGtwState.ONLINE:
            return [self, LGtwState.DISCONNECTED, LGtwState.RMTSH]
        if self == LGtwState.RMTSH:
            return [self, LGtwState.DISCONNECTED, LGtwState.ONLINE]
        return []

    @staticmethod
    def to_list():
        """Return a list of possible state values."""
        return [i.value for i in LGtwState]


class LoRaWANgtw(MongoModel):
    """LoRaWAN Gateway class.

    Attributes:
        name (str): LoRaWAN Gateway name
        lgtw_euid (EUI64Field): LoRaWAN Gateway EUID
        owner (EUI64Field): Owner of the lGTW
        name (CharField): A human-radable name of this LoRaWAN Gateway
        desc (CharField): A human-radable description of this LoRaWAN Gateway
        state (LGtwState): This lGTW state
        log (): Logging facility
        lgtw_config (DictField): Stores the conf. of the lGTW sent by the LNS
        last_seen_ts (IntegerField): Timestamp of the last message received
        last_seen (DateTimeField): Sequence number of the last message received
        connection (): WS connection
        rmtsh (bool): Implements interactive remote sheel
        prod  (bool):
        gps (bool): Implements GPS
        brand (str): lgtw brand
        model (str): lgtw model
        antenna (dict): Antenna params (type, placement, location, alt.)
        privacy (dict): Privacy settings (for status, location, owner)
        radio_data (list): Stats collected
        rx_messages (int): Number of received messages
        tx_messages (int): Number of transmitted messages

    Methods:
        is_connected(self): Return True if lGTW is connected
        is_rmt_shell(self): Return True if lGTW is in rmtsh state
        is_online(self): Return True if lGTW is online
        set_connected(self): Set lGTW to connected state
        set_disconnected(self): Set lGTW to disconnected state
        set_online(self): Set lGTW to online state
        set_rmt_shell(self): Set lGTW to remote shell state
        set_send_rtt_on(self): Send RTT message ON.
        set_send_rtt_off(self): Send RTT message OFF
        is_send_rtt_on(self): Return True if RTT messages are set to on
        to_dict(self): Return a JSON-serializable dic repr. the lGTW
    """

    lgtw_euid = EUI64Field(primary_key=True)  # 64 bit gtw identifier, EUI-64
    name = fields.CharField(required=True)
    desc = fields.CharField(required=False)
    owner = EUI64Field(required=True, default=DEFAULT_OWNER)
    lgtw_config = fields.DictField(required=True)
    # NOTE
    # lgtw_config data is sent by LNSS in reply to a "version"
    # message from the Basic Station using a "router_config" message
    # lgtw_config contains the following data:
    #   "NetID"      : [ INT, .. ]             // List of Integers
    #   "JoinEui"    : [ [INT, INT], .. ]       // List of Integer Ranges:
    #                                          // [beginning, end] inclusive
    #   "region"     : STRING                  // CharField, ref. to
    #                                          // regional settings Freq. Plan
    #                                          // e.g. "EU863", "US902", ...
    #   "hwspec"     : STRING                  // CharField
    #   "freq_range" : [ INT, INT ]            // Integer Range (list)
    #                                          //    [min, max] in (hz)
    #   "DRs"        : [ [INT, INT, INT], .. ]   // List of Int Triplets (list)
    #                                          //    [sf, bw, dnonly]
    #   "sx1301_conf": [ SX1301CONF, .. ]      // DictField
    #   "nocca"      : BOOL                    // BooleanField
    #   "nodc"       : BOOL                    // BooleanField
    #   "nodwell"    : BOOL                    // BooleanField
    lgtw_version = fields.DictField(required=False, blank=True)
    # lgtw version information is sent by the Basic Station at connection time
    # NOTE maybe there is no need to save it in the database
    ipaddr = fields.GenericIPAddressField(required=False, blank=True)
    last_seen = fields.DateTimeField(required=False)
    last_seen_ts = fields.IntegerField(required=False)
    # DEFAULTS
    rmtsh = False
    prod = False
    gps = False
    brand = "IMST"
    model = "iC880A"
    antenna = {"type": "xxx",
               "placement": "indoor",
               "location": [46, 11, 0]}
    # location e.g. PointField (long, lat)
    # (derived from GeoJSONField)
    connection = None
    privacy = {"status": "public", "location": "public", "owner": "public"}
    radio_data = []  # stats collected
    rx_messages = 0
    tx_messages = 0
    # Private attributes
    _state = LGtwState.DISCONNECTED
    # Protected attributes
    __send_rtt_on = True
    __has_pps_signal = False

    class Meta:
        """Define custom collection name."""

        collection_name = "lomm_lgtw"

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self.log = logging.getLogger("%s" % self.__class__.__module__)

    @property
    def state(self):
        """Return the state."""
        return self._state

    @state.setter
    def state(self, new_state):
        """Set the lgtw state."""
        if new_state not in self.state.next_valid:
            raise IOError("Invalid transistion %s -> %s"
                          % (self._state.value, new_state.value))
        if self._state != new_state:
            self.log.info("New LoRAWAN GTW %s state transition %s->%s",
                          self.lgtw_euid,
                          self.state.value,
                          new_state.value)
            self._state = new_state
            self.connection.lgtw_new_state(self._state, new_state)

    def is_connected(self):
        """Return if lGTW is connected."""
        return self.state == LGtwState.CONNECTED or LGtwState.ONLINE

    def is_rmt_shell(self):
        """Return if lGTW is in remote shell state."""
        return self.state == LGtwState.RMTSH

    def is_online(self):
        """Return if lGTW is online."""
        return self.state == LGtwState.ONLINE

    def set_connected(self):
        """Move lGTW to connected state."""
        self.state = LGtwState.CONNECTED

    def set_disconnected(self):
        """Move lGTW to disconnected state."""
        self.state = LGtwState.DISCONNECTED

    def set_online(self):
        """Move lGTW to online state."""
        self.state = LGtwState.ONLINE

    def set_rmt_shell(self):
        """Move lGTW to remote shell state."""
        self.state = LGtwState.RMTSH

    def set_send_rtt_on(self):
        """Send RTT message ON."""
        if not self.__send_rtt_on:
            self.__send_rtt_on = True
            self.connection.lgtw_rtt_on_set()

    def set_send_rtt_off(self):
        """Send RTT message OFF."""
        if self.__send_rtt_on:
            self.__send_rtt_on = False
            self.connection.lgtw_rtt_off_set()

    def is_send_rtt_on(self):
        """Return if RTT messages are set to ON."""
        return self.__send_rtt_on

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the PNFDev."""
        if not self.last_seen:
            self.last_seen = datetime.now()
        date = datetime.timestamp(self.last_seen)

        return {
            'name': self.name,
            'lgtw_euid': self.lgtw_euid.id6,
            'desc': self.desc,
            'state': self.state.value,
            'owner': str(self.owner),
            'lgtw_version': self.lgtw_version,
            'lgtw_config': self.lgtw_config,
            'last_seen': self.last_seen,
            'last_seen_ts': date,
            'ipaddr': self.ipaddr
            }
