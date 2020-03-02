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

import re

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField
from pymodm import validators

from empower.managers.lommmanager.datatypes.ldatatype  import LDataType, LDataTypeField

EUI64_PATTERN = re.compile("^([0-9a-fA-F]){2}(:([0-9a-fA-F]){2}){7}$")
"""Regular expression matching a well formed EUI using colon """

PLAIN_PATTERN = re.compile("^([0-9a-fA-F]){16}$")
"""Regular expression matching a well formed EUI no colon """

ID6_PATTERN   = re.compile("^([0-9a-fA-F]){1,4}(:([0-9a-fA-F]){1,4}){3}$")
"""Id6 regular expression matching representation after :: expansion"""

class EUI64(LDataType):
    """EUI64."""
    DEFAULT_VALUE = None
    BYTES = 8
    
    @property
    def id6(self):
        if self._value == 0:
            return "::0"
        s = "{0:#0{1}x}".format(self._value, self.BYTES*2+2)[2:]
        s = ''.join([ s[4*i:4*i+4]+':' for i in range(int(len(s)/4))])[:-1]
        # s = s.replace(":0000",":")
        # s = s.replace(":000",":")
        # s = s.replace(":00",":")
        # s = s.replace(":0",":")
        # s = s.replace("0000:",":")
        # if s[:3] == "000": s = s[3:]
        # if s[:2] == "00":  s = s[2:]
        # if s[:1] == "0":   s = s[1:]
        # s = s.replace(":::","::")        
        return s        
        
    @property
    def eui(self):
        if self._value == 0:
            return "00:00:00:00:00:00:00:00"
        s = "{0:#0{1}x}".format(self._value, self.BYTES*2 + 2)[2:]
        #print(s)
        s = ''.join([ s[2*i:2*i+2]+':' for i in range(int(len(s)/2))])[:-1] 
        #print(s)
        # s = s.replace(":0000",":")
        # s = s.replace(":000",":")
        # s = s.replace(":00",":")
        # s = s.replace(":0",":")
        # s = s.replace("0000:",":")
        # if s[:3] == "000": s = s[3:]
        # if s[:2] == "00":  s = s[2:]
        # if s[:1] == "0":   s = s[1:]
        # s = s.replace(":::","::")        
        return s        

    def __str__(self):
        s = "{0:#0{1}x}".format(self._value, self.BYTES*2 + 2)[2:]
        return ''.join([ s[2*i:2*i+2]+':' for i in range(int(len(s)/2))])[:-1]    
        
    def _to_raw_(self, data):
        """Returns the data as a DevID internal representation."""
        if isinstance(data, EUI64): 
            return int(data)
        elif isinstance(data, int):
            return data
        elif isinstance(data, bytes) and len(data) == self.BYTES*2:
            # raw
            return int.from_bytes(data, byteorder="little")
        elif isinstance(data, str):
            if data == "0":
                data = "::0"
            data = re.sub(r' ', '', data).lower()
            data = re.sub(r'[.:-]', ':', data)
            if EUI64_PATTERN.match(data) or PLAIN_PATTERN.match(data):
                """ if UID64 """
                data = re.sub(r':', '', data).lower()
                # data = data.split(":")
                data = [data[i:i+2] for i in range(0, len(data), 2)]
                return      ((int(data[0],16)<<56)|
                             (int(data[1],16)<<48)|
                             (int(data[2],16)<<40)|
                             (int(data[3],16)<<32)|
                             (int(data[4],16)<<24)|
                             (int(data[5],16)<<16)|
                             (int(data[6],16)<<8) |
                             (int(data[7],16)     ))
            else: 
                """ if ID6, first check if an :: expansion is needed """
                if data.count(':') == 2:
                    if data == '::':
                        data = [0,0,0,0,0,0,0,0]                        
                    elif data[0:2] == '::':
                        data = "0:0:0:" + data[2:]
                    elif data[-2:] == '::':
                        data = data[:-2] + ":0:0:0"
                    else:
                        p = data.find('::')
                        if p > 0:
                            data = data[0:p]+':0:0:'+data[p+2:]
                elif data.count(':') == 3:
                    if data[0:2] == '::':
                        data = "0:0:" + data[2:]
                    elif data[-2:] == '::':
                        data = data[:-2] + ":0:0"
                    else:
                        p = data.find('::')
                        if p > 0:
                            data = data[0:p]+':0:'+data[p+2:]
                if ID6_PATTERN.match(data):
                    data = data.split(':')                    
                    return    ((int(data[0],16)<<48)|
                               (int(data[1],16)<<32)|
                               (int(data[2],16)<<16)|
                               (int(data[3],16)    ))
                else:
                    raise ValueError('Invalid EUID: ' + data)
        

class EUI64Field(MongoBaseField):    
    """A field that stores WS URIs.

    This field only accepts EUID64 and ID6 str.
    """
                

    def __init__(self, verbose_name=None, mongo_name=None, **kwargs):
        """
        :parameters:
          - `verbose_name`: A human-readable name for the Field.
          - `mongo_name`: The name of this field when stored in MongoDB.

        .. seealso:: constructor for
                     :class:`~pymodm.base.fields.MongoBaseField`
        """
        super(EUI64Field, self).__init__(verbose_name=verbose_name,
                                       mongo_name=mongo_name,
                                       **kwargs)

        def validate_eui64(euid):
            try:
                EUI64(euid)
            except ValueError:                
                raise ValidationError('Invalid EUID: ' + euid)
        self.validators.append(validate_eui64)

        @classmethod
        def to_mongo(cls, value):
            """Convert value for storage."""
            try:
                return str(EUI64(value))
            except ValueError:
                msg = '%r is not a valid EUID.' % value
                raise ValidationError(msg)

        @classmethod
        def to_python(cls, value):
            """Convert value back to Python."""
            try:
                return EUI64(value)
            except ValueError:
                msg = '%r is not a valid EUID.'% value
                raise ValidationError(msg)
