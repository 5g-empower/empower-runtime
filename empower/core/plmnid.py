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

"""Public land mobile network identifier (PLMNID)."""

import re

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField
from empower.core.serialize import serializable_dict


@serializable_dict
class PLMNID:
    """Public land mobile network  identifier (PLMNID)."""

    def __init__(self, mcc="001", mnc="01"):

        if not re.findall(r'\b\d{3}\b', mcc):
            raise ValueError("Invalid MCC %s" % mcc)

        self.mcc = re.findall(r'\b\d{3}\b', mcc)[0]

        if not re.findall(r'\b\d{2,3}\b', mnc):
            raise ValueError("Invalid MCC %s" % mnc)

        self.mnc = re.findall(r'\b\d{2,3}\b', mnc)[0]

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "%s%s" % (self.mcc, self.mnc)

    def to_tuple(self):
        """Return a tuple representation of the object."""

        return (self.mcc, self.mnc)

    def to_dict(self):
        """Return a dict representation of the object."""

        return {
            "mcc": self.mcc,
            "mnc": self.mnc
        }

    def __bool__(self):
        return bool(self.mcc) and bool(self.mnc)

    def __str__(self):
        return self.to_str()

    def __len__(self):
        return len(self.to_str())

    def __hash__(self):
        return hash(self.to_str)

    def __eq__(self, other):
        if isinstance(other, PLMNID):
            return self.mcc == other.mcc and self.mnc == other.mnc
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

                if isinstance(value, PLMNID):
                    value = value.to_dict()

                return PLMNID(**value)

            except ValueError:
                msg = '%r is not a valid PLMN id.' % value
                raise ValidationError(msg)

        self.validators.append(validate_plmnid)

    @classmethod
    def to_mongo(cls, value):
        """Convert value for storage."""

        try:
            return value.to_dict()
        except ValueError:
            msg = '%r is not a valid PLMN id.' % value
            raise ValidationError(msg)

    @classmethod
    def to_python(cls, value):
        """Convert value back to Python."""

        try:

            if isinstance(value, PLMNID):
                value = value.to_dict()

            return PLMNID(**value)

        except ValueError:
            msg = '%r is not a valid PLMN id.' % value
            raise ValidationError(msg)
