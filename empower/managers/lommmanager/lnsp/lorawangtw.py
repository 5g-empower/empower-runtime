#!/usr/bin/env python3
#
# Copyright (c) 2019, CREATE-NET FBK, Trento, Italy
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
import json

from datetime import datetime
from pymodm import MongoModel, fields

from empower.datatypes.eui64 import EUI64Field, EUI64
from empower.managers.lommmanager.lnsp import DEFAULT_OWNER
from empower.managers.lommmanager.lnsp.lgtws_default_confs import LGTW_CONFIG_EU863_6CH

__author__     = "Cristina E. Costa"
__copyright__  = "Copyright 2019, FBK (https://www.fbk.eu)"
__credits__    = ["Cristina E. Costa"]
__license__    = "Apache License, Version 2.0"
__version__    = "1.0.0"
__maintainer__ = "Cristina E. Costa"
__email__      = "ccosta@fbk.eu"
__status__     = "Dev"

from enum import Enum, unique
@unique
class lgtwState(Enum):
    """ Enumerate lGTW STATES """
    DISCONNECTED = "disconnected"
    CONNECTED    = "connected"
    ONLINE       = "online"
    RMTSH        = "remote shell" # Remote Shell mode on
    
    @property
    def next_valid(self):
        """Return the next valid state for lgtw.
        
        The lgtw state machine is the following:
            disconnected <-> connected -> online
            online <-> rmsh
            online -> disconnected
        """
        if   self == lgtwState.DISCONNECTED:
            return [self, lgtwState.CONNECTED]
        elif self == lgtwState.CONNECTED:
            return [self, lgtwState.DISCONNECTED, lgtwState.ONLINE]
        elif self == lgtwState.ONLINE:
            return [self, lgtwState.DISCONNECTED, lgtwState.RMTSH]
        elif self == lgtwState.RMTSH:
            return [self, lgtwState.DISCONNECTED, lgtwState.ONLINE]
        else:
            return []
            
    @staticmethod
    def to_list():
        return [i.value for i in lgtwState]

class LoRaWANgtw(MongoModel):
    """ LoRaWAN Gateway class
    
    Attributes:
        owner (EUI64Field): Owner of the lGTW
        lgtw_euid (EUI):    LoRaWAN Gateway EUID
        name (CharField):   A human-radable name of this LoRaWAN Gateway
        desc (CharField):   A human-radable description of this LoRaWAN Gateway
        state (lgtwState):  This lGTW state
        log ():             Logging facility     
        lgtw_config (DictField):     Stores the configuration of the lGTW sent by the LNS       
        last_seen_ts (IntegerField): Timestamp of the last message received
        last_seen (DateTimeField):   Sequence number of the last message received
        connection ():      WS connection
        rmtsh (bool):       Implements interactive remote sheel
        prod  (bool):       
        gps (bool):         Implements GPS
        brand (str):        lgtw brand
        model (str):        lgtw model
        antenna (dict):     Antenna characteristics (type, placement, location, altitude
        privacy (dict):     Privacy settings (for status, location, owner)
        radio_data (list):  Stats collected
        rx_messages (int):  Number of received messages
        tx_messages (int):  Number of transmitted messages

    Methods:
        is_connected(self):     Return True if lGTW is connected
        is_rmt_shell(self):     Return True if lGTW is in remote shell state 
        is_online(self):        Return True if lGTW is online
        set_connected(self):    Set lGTW to connected state
        set_disconnected(self): Set lGTW to disconnected state
        set_online(self):       Set lGTW to online state
        set_rmt_shell(self):    Set lGTW to remote shell state
        set_send_rtt_on(self):  Send RTT message ON.
        set_send_rtt_off(self): Send RTT message OFF
        is_send_rtt_on(self):   Return True if RTT messages are set to on
        to_dict(self):          Return a JSON-serializable dictionary representing the LoRaWAN gtw
    """

    # ALIAS = "lgtws"
    # TBL_CONFIG = "TblLoRaRadioConfig"
    lgtw_euid     = EUI64Field(primary_key=True) # 64 bit gateway identifier, EUI-64
    lgtw_config   = fields.DictField(required=True)
    # Dict sent in reply by LNSS to msg_type="version" (msg_type="router_config")
    #   "NetID"      : [ INT, .. ]             // List of Integers
    #   "JoinEui"    : [ [INT,INT], .. ]       // List of Integer Ranges: [beginning,end] inclusive
    #   "region"     : STRING                  // CharField, ref. to regional settings e.g. "EU863", "US902", .. (Frequency Plan)
    #   "hwspec"     : STRING                  // CharField
    #   "freq_range" : [ INT, INT ]            // Integer Range (list) [min, max] in (hz)
    #   "DRs"        : [ [INT,INT,INT], .. ]   // List of Integer Triplets (list) [sf,bw,dnonly]
    #   "sx1301_conf": [ SX1301CONF, .. ]      // DictField
    #   "nocca"      : BOOL                    // BooleanField
    #   "nodc"       : BOOL                    // BooleanField
    #   "nodwell"    : BOOL                    // BooleanField
    owner         = EUI64Field(required=True, default=DEFAULT_OWNER)
    name          = fields.CharField(required=True)
    desc          = fields.CharField(required=False)
    lgtw_version  = fields.DictField(required=False, blank=True)
    ipaddr        = fields.GenericIPAddressField(required=False, blank=True)
    last_seen     = fields.DateTimeField(required=False)
    last_seen_ts  = fields.IntegerField(required=False)
    rmtsh         = False
    prod          = False
    gps           = False
    brand         = "IMST"
    model         = "iC880A"
    antenna       = {"type":"xxx","placement":"indoor","location":[46,11],"altitude":0} # location e.g. PointField (long,lat) (derived from GeoJSONField)
    connection    = None
    privacy       = {"status":"public","location":"public", "owner":"public"}
    radio_data    = [] # stats collected
    rx_messages   = 0
    tx_messages   = 0 
    # Private attributes
    _state        = lgtwState.DISCONNECTED
    # Protected attributes
    __send_rtt_on    = True
    __has_pps_signal = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)   
        self.log = logging.getLogger("%s" % self.__class__.__module__)

    @property
    def state(self):
        """Return the state."""
        return self._state
        
    # @state.setter
    # def state(self, state):
    #     """Set the lgtw state."""
    #     method = "_%s_%s" % (self.state, state)
    #     if hasattr(self, method):
    #         self.log.info("New LoRAWAN RGTW %s state transition %s->%s", self.lgtw_euid, self.state, state)
    #         callback = getattr(self, method)
    #         callback()            
    #     else:
    #         raise IOError("Invalid transistion %s -> %s" % (self.state, state))        
    #     self.connection.lgtw_new_state(self.state, state)
    @state.setter
    def state(self, new_state):
        """Set the lgtw state."""
        if new_state not in self.state.next_valid:
            raise IOError("Invalid transistion %s -> %s" % (self.state.value, state.value))
        elif self.state != new_state: 
            self.log.info("New LoRAWAN GTW %s state transition %s->%s", 
                            self.lgtw_euid, self.state.value, new_state.value)
            self._state = new_state
            self.connection.lgtw_new_state(self.state, new_state)   
        
    # """ Valid State Transisions """
    # def _online_online(self):
    #     # null transition
    #     pass

    # def _disconnected_disconnected(self):
    #     # null transition
    #     pass

    # def _disconnected_connected(self):
    #     # set new state
    #     self._state = lgtwState.CONNECTED

    # def _connected_disconnected(self):        
    #     # set new state
    #     self._state = lgtwState.DISCONNECTED

    # def _online_disconnected(self):
    #     # set new state
    #     self._state = lgtwState.DISCONNECTED

    # def _connected_online(self):
    #     # set new state
    #     self._state = lgtwState.ONLINE
        
    # def _online_rmtsh(self):
    #     # set new state
    #     self._state = lgtwState.RMTSH

    # def _rmtsh_online(self):
    #     # set new state
    #     self._state = lgtwState.ONLINE


    def is_connected(self):
        """Return if lGTW is connected"""
        return self.state == lgtwState.CONNECTED or lgtwState.ONLINE

    def is_rmt_shell(self):
        """Return if lGTW is in remote shell state """
        return self.state == lgtwState.RMTSH

    def is_online(self):
        """Return if lGTW is online"""
        return self.state == lgtwState.ONLINE

    def set_connected(self):
        """Move lGTW to connected state."""
        self.state = lgtwState.CONNECTED

    def set_disconnected(self):
        """Move lGTW to disconnected state."""
        self.state = lgtwState.DISCONNECTED

    def set_online(self):
        """Move lGTW to online state."""
        self.state = lgtwState.ONLINE
        
    def set_rmt_shell(self):
        """Move lGTW to remote shell state."""
        self.state = lgtwState.RMTSH
        
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
        """Return if RTT messages are set to ON"""
        return self.__send_rtt_on

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the PNFDev."""
        if not self.last_seen:
            self.last_seen = datetime.now()
        date = datetime.timestamp(self.last_seen) 
            
        if self.connection:
            connection = self.connection.to_dict()
        else:
            connection = None

        return {
                'lgtw_euid':   str(self.lgtw_euid),
                'desc':         self.desc,
                'state':        self.state.value, #CC changed
                'owner':        str(self.owner),
                'lgtw_version':      self.lgtw_version,
                'lgtw_config':  self.lgtw_config,
                'last_seen':    self.last_seen,
                'last_seen_ts': date,
                'connection':   connection
               }