#!/usr/bin/env python3
#
# Copyright (c) 2020 Cristina Costa
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
"""LoRaWAN End Device."""

import logging

from datetime import datetime
from pymodm import MongoModel, fields


from empower.datatypes.eui64 import EUI64Field
from empower.managers.lommmanager.lnsp import DEFAULT_OWNER

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
class enddevState(Enum):
    """ Enumerate enddev STATES """
    GENERIC     = "generic"
    COMISSIONED = "comissioned"
    ACTIVATED   = "activated"
    
    @property
    def next_valid(self):
        """Return the next valid state for lgtw.
        
        The lgtw state machine is the following:
            generic <-> comissioned <-> activated
        """
        if   self == enddevState.GENERIC:
            return [self, enddevState.COMISSIONED]
        elif self == enddevState.COMISSIONED:
            return [self, enddevState.GENERIC, enddevState.ACTIVATED]
        elif self == enddevState.ACTIVATED:
            return [self, enddevState.COMISSIONED]
        else:
            return []
            
    @staticmethod
    def to_list():
        return [i.value for i in enddevState]

class LoRaWANEndDev(MongoModel):
    """An LoRaWAN End Device.

    Attributes:
        euid: This LNS EUID
        [...]
        desc: A human-radable description of this Device (str)
        log:  logging facility
    """
    devEUI       = EUI64Field(primary_key=True) # 64 bit lEndDev identifier, EUI-64
    devAddr      = fields.CharField(required=False)   
    joinEUI      = EUI64Field(required=False, blank=True) # 64 bit Join Server identifier (appEUI for v<1.1), EUI-64
    appKey       = fields.CharField(required=False, blank=True)
    nwkKey       = fields.CharField(required=False, blank=True)
    appSKey      = fields.CharField(required=False, blank=True)
    nwkSKey      = fields.CharField(required=False, blank=True)
    ##TODO Add session keys: <v1.1> NwsSKey, AppSKey
    lversion     = fields.CharField(required=True, blank=True, default="1.0")
    owner        = fields.CharField(required=True, blank=True, default=DEFAULT_OWNER)
    state        = fields.CharField(required=True, blank=True, default="enddevState.GENERIC")
    activation   = fields.CharField(required=True, blank=True, default="ABP") # OTAA or ABP
    dev_class    = fields.CharField(required=True, blank=True, default="ClassA") # A, B, C
    desc         = fields.CharField(required=False, blank=True)
    tags         = fields.ListField(required=False, blank=True) 
    lgtws_range  = fields.ListField(required=False, blank=True) 
    last_seen    = 0
    last_seen_ts = 0
    frames_up    = 0
    frames_down  = 0
    frame_count  = 0 ##REVIEW 
    location      = fields.ListField(required=False, blank=True) 
    altitude      = fields.IntegerField(required=False, blank=True)
    fcntChecks    = fields.BooleanField(required=False, blank=True, default=False), # frame_counter_checks - REVIEW False vs. True
    fcntWidth     = fields.CharField(required=False, blank=True, default="16bit") # frame_counter_size "16bit"/"32bit" else None, # 16bit or 32bit
    payloadFormat = fields.CharField(required=False, blank=True) 


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._serving_lgtw  = None
        self._type  = self.activation # ABR or OTA
        
        self.__state = enddevState.GENERIC
        self.__connection = None
        self.log = logging.getLogger("%s" % self.__class__.__module__)
        return

    @property
    def state(self):
        """Return the state."""
        return self.__state

    @state.setter
    def state(self, state):
        """Set the Device state."""
        if new_state not in self.state.next_valid:
            raise IOError("Invalid transistion %s -> %s" % (self.state.value, state.value))
        elif self.state != new_state: 
            self.state = new_state
            self.log.info("New LoRAWAN End Device %s state transition %s->%s", 
                            self.devEUI, self.state.value, new_state.value)
            self.connection.lgtw_new_state(self.state, new_state)  
        # if self.state:
        #     method = "__%sdev_%s_%s" % (self._type, self._state, state)
        # if hasattr(self, method):
        #     callback = getattr(self, method)
        #     callback()
        #     self.log.info("New LoRAWAN End Device %s state transition %s->%s", 
        #                     self.devEUI, self.state.value, new_state.value)
        #     return
        # raise IOError("Invalid transistion %s -> %s" % (self.state, state))
        
    """ Device Commissioning """
    def __ABRdev_generic_commissioned(self):
        self._state = enddevState.ACTIVATED # for ABR
        return self._state
        
    def __OTAdev_generic_commissioned(self):
        self._state = enddevState.COMISSIONED # for OTA
        return self._state

    """ Device Decommissioning """
    def __ABRdev_commissioned_generic(self):
        return self._state
        
    def __OTAdev_commissioned_generic(self):
        self._state = enddevState.GENERIC # for OTA
        return self._state
            
    """ Device Join """
    def __ABRdev_commissioned_activated(self):    
        return self._state
        
    def __OTAdev_commissioned_activated(self):
        self._state = enddevState.ACTIVATED # for OTA    
        return self._state
    
    """ OTA Device Exit """        
    def __OTAdev_activated_commissioned(self):
        self._state = enddevState.COMISSIONED # for OTA    
        return self._state
        
    @property
    def serving_lgtw(self):
        """Return the LoRaGTW serving this lEndDev"""
        return self._serving_lgtw

    @serving_lgtw.setter
    def serving_lgtw(self, serving_lgtw):
        """ Update lGTW of lEndDev."""
        self._serving_lgtw = serving_lgtw
        # check if joined?        
        
    def to_dict(self):
        """Return a JSON-serializable dictionary representing the LoRaWAN Device."""

        date = datetime.fromtimestamp(self.last_seen_ts) \
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
        out =  {"devEUI":       self.devEUI,
                "joinEUI":      self.joinEUI,
                "appKey":       self.appKey,
                "nwkKey":       self.nwkKey,
                "appSKey":      self.appSKey,
                "nwkSKey":      self.nwkSKey,
                'last_seen':    self.last_seen,
                'last_seen_ts': date,
                'state':        self.state,
                'lversion':     self.lversion, 
                'owner':        self.owner,    
                'state':        self.state.value,    
                'activation':   self.activation,
                'dev_class':    self.dev_class ,
                'location':     self.location,
                'altitude':     self.altitude,
                # 'fcntChecks':   self.fcntChecks,
                'fcntWidth':    self.fcntWidth,
                'payloadFormat': self.payloadFormat
                }
        if self.tags:
            out['tags'] = self.tags
        if self.tags:
            out['lgtws_range'] = self.lgtws_range
        if self.tags:
            out['devAddr'] = self.devAddr
                
        return out

    def __eq__(self, other):
        if isinstance(other, self.__class__.__name__):
            return self.devEUI == other.devEUI
        return False

    def __str__(self):
        return "LoRaWAN Device %s, label=%s, owner=%s" \
               % (str(self.devEUI), self.desc, self.owner)

    def is_activated(self):
        """Return true if the device is connected"""
        return self.state == enddevState.ACTIVATED

    def is_comissioned(self):
        """Return true if the device is comissioned"""
        return self.state == enddevState.COMISSIONED

    def is_generic(self):
        """Return true if the device is generic"""
        return self.state == enddevState.GENERIC

    def handle_add_lgtw(self, euid):
        """ Save whe the lEndDev is seen by a new lGTW."""
        if str(EUID64(euid)) not in self.lgtws_range:
            self.lgtws_range.append(euid)

    def handle_join_response(self):
        """ Handle Join Request Response """
        self.state = enddevState.ACTIVATED

    @property
    def connection(self):
        """Get the connection assigned to this Device."""
        return self.__connection

    @connection.setter
    def connection(self, connection):
        """Set the connection assigned to this Device."""
        self.__connection = connection
        return "%s" % self.addr

    def __hash__(self):
        return hash(self.addr)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + str(self) + "')"
