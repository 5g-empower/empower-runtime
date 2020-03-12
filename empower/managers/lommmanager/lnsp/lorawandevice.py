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
"""LoRaWAN End Device."""

# NOTE
# The implementation supports both 1.0.x and 1.1.x LoRaWAN versions
# of the specification. This implementation use the 1.1.x keys
# and EUI name definitions. The below table shows the names equivalence
# between versions:
#     +---------+-------------+
#     |  1.0.x  |  1.1.1      |
#     +=========+=============+
#     | devEUI  | devEUI      |
#     +---------+-------------+
#     | appEUI  | appEUI      |
#     +---------+-------------+
#     | N/A     | appKey      |
#     +---------+-------------+
#     | appKey  | nwkKey      |
#     +---------+-------------+
#     | nwkSKey | fNwkSIntKey |
#     +---------+-------------+
#     | nwkSKey | sNwkSIntKey |
#     +---------+-------------+
#     | nwkSKey | nwkSEncKey  |
#     +---------+-------------+
#     | nwkSKey | appSKey     |
#     +---------+-------------+

import logging
import re

from datetime import datetime
from enum import Enum, unique
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from pymodm import validators

from empower.core.eui64 import EUI64Field, EUI64
from empower.managers.lommmanager.lnsp import DEFAULT_OWNER


def validator_for_hex(value):
    """Validate if the value is hex."""
    if value and not re.match(r'^([0-9a-fA-F]+)$', value):
        raise ValidationError("Not an hexadecimal value %s" % value)


def validator_for_location(coordinates):
    """Validate if value is a list of double numbers."""
    if not (isinstance(coordinates, (list, tuple)) and
            len(coordinates) == 3):
        raise ValidationError('Point is not a triple: %r' % coordinates)
    validate_number = validators.validator_for_type(
        (float, int), 'Coordinates [lat, long, alt]')
    validate_number(coordinates[0])
    # latitude
    validate_number(coordinates[1])
    # longitude
    validate_number(coordinates[2])
    # altitude


class LowerCharField(fields.CharField):
    """A field that stores unicode strings but before convers to lowercase."""

    def to_mongo(self, value):
        """Convert value to lowercase before being saved on mongodb."""
        return value.lower()

    def to_python(self, value):
        """Convert value to lowercase before being saved in python var."""
        return value.lower()


@unique
class LEndDevState(Enum):
    """Enumerate enddev States."""

    GENERIC = "generic"
    COMISSIONED = "comissioned"
    ACTIVATED = "activated"

    @property
    def next_valid(self):
        """Return the next valid state for lgtw.

        The lgtw state machine applies to OTA devices only
        and is the following (ref. lorawan-backend-interfaces-v1.0):

                 commissioning                   join
        generic ----------------> comissioned ---------> activated
            ^                          |    ^        |
            |   decommissioning        |    |  exit  |
            ----------------------------    ----------
        """
        if self == LEndDevState.GENERIC:
            return [self, LEndDevState.COMISSIONED]
        if self == LEndDevState.COMISSIONED:
            return [self, LEndDevState.GENERIC, LEndDevState.ACTIVATED]
        if self == LEndDevState.ACTIVATED:
            return [self, LEndDevState.COMISSIONED]
        return []

    @staticmethod
    def to_list():
        """Return a list of possible state values."""
        return [i.value for i in LEndDevState]


class LoRaWANEndDev(MongoModel):
    """An LoRaWAN End Device.

    Attributes:
        euid: This LNS EUID
        [...]
        desc: A human-radable description of this Device (str)
        log: logging facility
    """

    dev_eui = EUI64Field(primary_key=True)
    # 64 bit lEndDev identifier, EUI-64
    dev_addr = LowerCharField(required=False, blank=True,
                              min_length=8, max_length=8,
                              validators=[validator_for_hex])
    # 32 bit shirt devAddr identifier
    net_id = LowerCharField(required=False, blank=True,
                            min_length=6, max_length=6,
                            validators=[validator_for_hex])
    # TODO check netID format
    # 24-bit value used for identifying LoRaWAN network,
    # for non-collaborating network: can use the 0x000000 or 0x000001.
    lversion = LowerCharField(required=True, blank=True, default="1.0")
    # LoRaWAN version
    label = fields.CharField(required=False, blank=True)
    desc = fields.CharField(required=False, blank=True,
                            verbose_name="description")
    tags = fields.ListField(required=False, blank=True)
    owner = fields.CharField(required=True, blank=True, default=DEFAULT_OWNER)
    join_eui = EUI64Field(required=False, blank=True)
    # 64 bit Join Server identifier (appEUI for v<1.1), EUI-64
    activation = fields.CharField(required=True, blank=True, default="ABP",
                                  choices=["OTA", "ABP"])
    dev_class = fields.CharField(required=True, blank=True, default="ClassA",
                                 choices=["ClassA", "ClassB", "ClassC"],
                                 verbose_name="device class")
    lgtws_range = fields.ListField(required=False, blank=True)
    app_key = LowerCharField(required=False, blank=True,
                             min_length=32, max_length=32,
                             validators=[validator_for_hex])
    nwk_key = LowerCharField(required=False, blank=True,
                             min_length=32, max_length=32,
                             validators=[validator_for_hex])
    app_s_key = LowerCharField(required=False, blank=True,
                               min_length=32, max_length=32,
                               validators=[validator_for_hex])
    nwk_s_enc_key = LowerCharField(required=False, blank=True,
                                   min_length=32, max_length=32,
                                   validators=[validator_for_hex])
    f_nwk_s_int_key = LowerCharField(required=False, blank=True,
                                     min_length=32, max_length=32,
                                     validators=[validator_for_hex])
    s_nwk_s_int_key = LowerCharField(required=False, blank=True,
                                     min_length=32, max_length=32,
                                     validators=[validator_for_hex])
    location = fields.ListField(required=False, blank=True,
                                verbose_name="[latitude, longitude, altitude]",
                                validators=[validator_for_location])
    fcnt_checks = fields.BooleanField(required=False,
                                      blank=True, default=False)
    # frame_counter_checks - REVIEW False vs. True
    fcnt_size = fields.CharField(required=False, blank=True, default="16bit",
                                 choices=["16bit", "32bit"])
    # frame_counter_size (FCnt)
    payloadFormat = fields.CharField(required=False, blank=True)
    # e.g. "CayenneLPP"
    last_seen = 0
    last_seen_ts = 0
    frames_up = 0
    frames_down = 0
    frame_count = 0   # FCnt

    class Meta:
        """Define a custom collection name, ignore unknown fields."""

        collection_name = "lomm_lenddev"
        ignore_unknown_fields = True

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        if self.activation == "OTA":
            self.__state = LEndDevState.GENERIC
        else:
            self.__state = LEndDevState.ACTIVATED
        self._serving_lgtw = None
        self._type = self.activation   # ABR or OTA
        self.__connection = None
        self.log = logging.getLogger("%s" % self.__class__.__module__)

    @property
    def state(self):
        """Return the state."""
        return self.__state

    @state.setter
    def state(self, new_state):
        """Set the Device state."""
        if self.activation == "OTA":
            if new_state not in self.state.next_valid:
                raise IOError("Invalid transistion %s -> %s"
                              % (self.state.value, new_state.value))
            if self.state != new_state:
                self.state = new_state
                self.log.info(
                    "New LoRAWAN End Device %s state transition %s->%s",
                    self.dev_eui, self.state.value, new_state.value)
                self.connection.lgtw_new_state(self.state, new_state)

    @property
    def serving_lgtw(self):
        """Return the LoRaGTW serving this lEndDev."""
        return self._serving_lgtw

    @serving_lgtw.setter
    def serving_lgtw(self, serving_lgtw):
        """Update lGTW of lEndDev."""
        self._serving_lgtw = serving_lgtw
        # TODO add check if joined

    def to_dict(self):
        """Return a dictionary representing the LoRaWAN Device.

        The dictionary is JSON-serializable
        """
        date = datetime.fromtimestamp(self.last_seen_ts) \
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        out = {"devEUI": self.dev_eui.id6,
               "joinEUI": self.join_eui.id6,
               "devAddr": self.dev_addr,
               "netID": self.net_id,
               "appKey": self.app_key,
               "desc": self.desc,
               "nwkKey": self.nwk_key,
               "appSKey": self.app_s_key,
               "nwkSEncKey": self.nwk_s_enc_key,
               "sNwkSIntKey": self.f_nwk_s_int_key,
               "fNwkSIntKey": self.s_nwk_s_int_key,
               "devClass": self.dev_class,
               "lVersion": self.lversion,
               "owner": self.owner,
               "state": self.state.value,
               "activation": self.activation,
               "location": self.location,
               "fCntChecks": self.fcnt_checks,
               "fCntSize": self.fcnt_size,
               "payloadFormat": self.payloadFormat,
               "last_seen": self.last_seen,
               "last_seen_ts": date,
               "frames_up": self.frames_up,
               "frames_down": self.frames_down,
               "frame_count": self.frame_count,
               }
        if self.tags:
            out["tags"] = self.tags
        if self.lgtws_range:
            out["lgtwsRange"] = self.lgtws_range
        if self.dev_addr:
            out["devAddr"] = self.dev_addr

        return out

    def __eq__(self, other):
        """Return if the two istances are equal.

        The two instances of lEndDevs are considered
        equal if their devEUI is equal.
        """
        if isinstance(other, self.__class__.__name__):
            return self.dev_eui == other.dev_eui
        return False

    def __str__(self):
        """Return a string representing the lEndDev."""
        return "LoRaWAN Device %s, label=%s, owner=%s" \
               % (self.dev_eui.id6, self.desc, self.owner)

    def is_activated(self):
        """Return true if the device is connected."""
        return self.state == LEndDevState.ACTIVATED

    def is_comissioned(self):
        """Return true if the device is comissioned."""
        return self.state == LEndDevState.COMISSIONED

    def is_generic(self):
        """Return true if the device is generic."""
        return self.state == LEndDevState.GENERIC

    def handle_add_lgtw(self, euid):
        """Save whe the lEndDev is seen by a new lGTW."""
        if str(EUI64(euid)) not in self.lgtws_range:
            self.lgtws_range.append(euid)

    def handle_join_response(self):
        """Handle Join Request Response."""
        self.state = LEndDevState.ACTIVATED

    @property
    def connection(self):
        """Get the connection assigned to this Device."""
        return self.__connection

    @connection.setter
    def connection(self, connection):
        """Set the connection assigned to this Device."""
        self.__connection = connection

    def __ne__(self, other):
        """Return true if the two istances are not equal."""
        return not self.__eq__(other)

    def __repr__(self):
        """Return a representation of the object."""
        return self.__class__.__name__ + "('" + str(self) + "')"
