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

"""Base device class."""

import logging
from pymodm import MongoModel, fields

from empower.datatypes.EUID import EUIDField
from empower.datatypes.IPAddress import IPAddressField

__author__     = "Cristina E. Costa"
__copyright__  = "Copyright 2019, FBK (https://www.fbk.eu)"
__credits__    = ["Cristina E. Costa"]
__license__    = "Apache License, Version 2.0"
__version__    = "1.0.0"
__maintainer__ = "Cristina E. Costa"
__email__      = "ccosta@fbk.eu"
__status__     = "Dev"


class LNS(MongoModel):
    """LNS class.

    Attributes:
        euid: This LNS EUID
        ip:   This LNS IP address (IPAddress)
        port: This LNS port
        desc: A human-radable description of this Device (str)
        log:  logging facility
    """

    euid = EUIDField(primary_key=True)
    ip   = IPField(required=True)
    port = fields.IntField(required=True)
    gtws = fields.ListField(required=True)
    desc = fields.CharField(required=True)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.log = logging.getLogger("%s" % self.__class__.__module__)
        
    def to_str(self):
        """Return an ASCII representation of the object."""
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
