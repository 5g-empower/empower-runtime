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

"""Public land mobile network  identifier (PLMNID)."""

import re

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField


class PLMNID:
    """Public land mobile network  identifier (PLMNID)."""

    def __init__(self, plmnid=None):

        if not plmnid:
            plmnid = bytes(16)

        if isinstance(plmnid, str):
            allowed = re.compile(r'^[f0-9]+$', re.VERBOSE | re.IGNORECASE)
            if allowed.match(plmnid) is None:
                raise ValueError("Invalid PLMNID name")
            self.plmnid = plmnid.lower()
        elif isinstance(plmnid, bytes):
            self.plmnid = plmnid[1:].hex()
        elif isinstance(plmnid, PLMNID):
            self.plmnid = str(plmnid)
        else:
            raise ValueError("PLMNID must be a string")

    def to_raw(self):
        """ Return the bytes represenation of the PLMNID """

        return int(self.plmnid, 16).to_bytes(4, byteorder='big')

    def to_str(self):
        """Return an ASCII representation of the object."""

        return self.plmnid

    def __bool__(self):
        return bool(self.plmnid)

    def __str__(self):
        return self.to_str()

    def __len__(self):
        return len(self.plmnid)

    def __hash__(self):
        return hash(self.plmnid)

    def __eq__(self, other):
        if isinstance(other, PLMNID):
            return self.plmnid == other.plmnid
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"


class PLMNIDField(MongoBaseField):
    """A field that stores PLMNIDs."""

    def __init__(self, verbose_name=None, mongo_name=None, **kwargs):

        super(PLMNIDField, self).__init__(verbose_name=verbose_name,
                                          mongo_name=mongo_name,
                                          **kwargs)

        def validate_plmnid(value):

            try:
                PLMNID(value)
            except ValueError:
                msg = '%r is not a valid PLMN id.' % value
                raise ValidationError(msg)

        self.validators.append(validate_plmnid)

    @classmethod
    def to_mongo(cls, value):
        """Convert value for storage."""

        try:
            return str(value)
        except ValueError:
            msg = '%r is not a valid PLMN id.' % value
            raise ValidationError(msg)

    @classmethod
    def to_python(cls, value):
        """Convert value back to Python."""

        try:
            return PLMNID(value)
        except ValueError:
            msg = '%r is not a valid PLMN id.' % value
            raise ValidationError(msg)
