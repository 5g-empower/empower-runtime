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
"""EUI64 data format."""

import re

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField
from pymodm import validators

EUI64_PATTERN = re.compile("^([0-9a-fA-F]){2}(:([0-9a-fA-F]){2}){7}$")
"""Regular expression matching a well formed EUI using colon """

PLAIN_PATTERN = re.compile("^([0-9a-fA-F]){16}$")
"""Regular expression matching a well formed EUI no colon """

ID6_PATTERN = re.compile("^([0-9a-fA-F]){1,4}(:([0-9a-fA-F]){1,4}){3}$")
"""Id6 regular expression matching representation after :: expansion"""


class EUI64():
    """EUI64."""

    DEFAULT_VALUE = None
    BYTES = 8

    def __init__(self, data=None):
        if data is None:
            # set to default
            self._value = self.DEFAULT_VALUE
        else:
            self._value = self._to_raw_(data)

    @property
    def id6(self):
        """Return data in ID6 format."""
        if self._value == 0:
            return "::0"
        out = "{0:#0{1}x}".format(self._value, self.BYTES*2+2)[2:]
        out = [out[4*i:4*i+4]+':' for i in range(int(len(out)/4))]
        out = ''.join(out)[:-1]
        return out

    @property
    def eui64(self):
        """Return data in EUI format."""
        if self._value == 0:
            return "00:00:00:00:00:00:00:00"
        out = "{0:#0{1}x}".format(self._value, self.BYTES*2 + 2)[2:]
        out = [out[2*i:2*i+2]+':' for i in range(int(len(out)/2))]
        out = ''.join(out)[:-1]
        return out

    def __str__(self):
        """Return EUID in string format."""
        if self._value:
            out = "{0:#0{1}x}".format(self._value, self.BYTES*2 + 2)[2:]
            out = [out[2*i:2*i+2]+':' for i in range(int(len(out)/2))]
            return ''.join(out)[:-1]
        return ""

    def _to_raw_(self, data):
        """Return the data as internal representation."""
        if isinstance(data, int):
            return data
        if isinstance(data, EUI64):
            return int(data)
        if isinstance(data, bytes) and len(data) == self.BYTES*2:
            # raw data
            return int.from_bytes(data, byteorder="little")
        if not isinstance(data, str):
            raise ValueError('Invalid EUID: ' + repr(data))
        data = re.sub(r' ', '', data).lower()
        # eliminate spaces and ":", ".", "-"
        data = re.sub(r'[.:-]', ':', data)
        # eliminate spaces and ":", ".", "-"
        if EUI64_PATTERN.match(data) or PLAIN_PATTERN.match(data):
            data = re.sub(r':', '', data).lower()
            # data = data.split(":")
            data = [data[i:i+2] for i in range(0, len(data), 2)]
            return ((int(data[0], 16) << 56) |
                    (int(data[1], 16) << 48) |
                    (int(data[2], 16) << 40) |
                    (int(data[3], 16) << 32) |
                    (int(data[4], 16) << 24) |
                    (int(data[5], 16) << 16) |
                    (int(data[6], 16) << 8) |
                    (int(data[7], 16)))
        # first check if an :: expansion is needed in ID6
        if data in ["0", "::"]:
            data = "0:0:0:0"
        if data.count(':') == 2:
            data = re.sub('^::', '0:0:0:', data)
            data = re.sub('::$', ':0:0:0', data)
            data = re.sub('::', ':0:0:', data)
        elif data.count(':') == 3:
            data = re.sub('^::', '0:0:', data)
            data = re.sub('::$', ':0:0', data)
            data = re.sub('::', ':0:', data)
        if ID6_PATTERN.match(data):
            data = data.split(':')
            return ((int(data[0], 16) << 48) |
                    (int(data[1], 16) << 32) |
                    (int(data[2], 16) << 16) |
                    (int(data[3], 16)))
        raise ValueError('Invalid EUID: ' + repr(data))

    def __eq__(self, other):
        other = EUI64(other)
        return other._value == self._value


class EUI64Field(MongoBaseField):
    """A field that stores WS URIs.

    This field only accepts EUID64 or ID6 str.
    """

    def __init__(self, verbose_name=None, mongo_name=None, **kwargs):
        """Init EUID data.

        :parameters:
          - "verbose_name": A human-readable name for the Field.
          - "mongo_name": The name of this field when stored in MongoDB.
        """
        super(EUI64Field, self).__init__(verbose_name=verbose_name,
                                         mongo_name=mongo_name,
                                         **kwargs)

        def validate_eui64(euid):
            try:
                EUI64(euid)
            except ValueError:
                raise ValidationError('Invalid EUID: ' + euid)
            validators.append(validate_eui64)

        # @classmethod
        # def to_mongo(cls, value):
        #     """Convert value for storage."""
        #     try:
        #         return str(EUI64(value))
        #     except ValueError:
        #         msg = '%r is not a valid EUID.' % value
        #         raise ValidationError(msg)

        # @classmethod
        # def to_python(cls, value):
        #     """Convert value back to Python."""
        #     try:
        #         return EUI64(value)
        #     except ValueError:
        #         msg = '%r is not a valid EUID.' % value
        #         raise ValidationError(msg)
