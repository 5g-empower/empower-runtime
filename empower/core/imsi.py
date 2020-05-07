#!/usr/bin/env python3
#
# Copyright (c) 2020 Roberto Riggio
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

"""international mobile subscriber identity (IMSI)."""

import re

from stdnum import numdb
from stdnum.util import clean, isdigits

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField

from empower.core.plmnid import PLMNID
from empower.core.serialize import serializable_string


@serializable_string
class IMSI:
    """international mobile subscriber identity (IMSI)."""

    def __init__(self, imsi):

        imsi = clean(imsi, ' -').strip().upper()

        if not isdigits(imsi):
            raise ValueError("Invalid IMSI %s" % imsi)

        if len(imsi) not in (14, 15):
            raise ValueError("Invalid IMSI length %s" % imsi)

        if len(tuple(numdb.get('imsi').split(imsi))) < 2:
            raise ValueError("Invalid IMSI length %s" % imsi)

        self.info = dict(imsi=imsi)

        mcc_info, mnc_info, msin_info = numdb.get('imsi').info(imsi)

        self.info['mcc'] = mcc_info[0]
        self.info.update(mcc_info[1])
        self.info['mnc'] = mnc_info[0]
        self.info.update(mnc_info[1])
        self.info['msin'] = msin_info[0]
        self.info.update(msin_info[1])

    @property
    def plmnid(self):
        """Get mcc."""

        return PLMNID("%s%s" % (self.mcc, self.mnc))

    @property
    def mcc(self):
        """Get mcc."""

        return self.info['mcc']

    @property
    def mnc(self):
        """Get mnc."""

        return self.info['mnc']

    @property
    def msin(self):
        """Get msin."""

        return self.info['msin']

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "%s%s%s" % (self.mcc, self.mnc, self.msin)

    def to_tuple(self):
        """Return a tuple representation of the object."""

        return tuple(self.info.values())

    def to_dict(self):
        """Return a dict representation of the object."""

        return self.info

    def __str__(self):
        return self.to_str()

    def __len__(self):
        return len(self.to_str())

    def __hash__(self):
        return hash(self.to_str())

    def __eq__(self, other):
        if isinstance(other, IMSI):
            return self.to_str() == other.to_str()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"


class IMSIField(MongoBaseField):
    """A field that stores IMSIs."""

    def __init__(self, verbose_name=None, mongo_name=None, **kwargs):

        super(IMSIField, self).__init__(verbose_name=verbose_name,
                                          mongo_name=mongo_name,
                                          **kwargs)

        def validate_imsi(value):

            try:

                if isinstance(value, IMSI):
                    value = value.to_str()

                return PLMNID(value)

            except ValueError:
                msg = '%r is not a valid IMSI.' % value
                raise ValidationError(msg)

        self.validators.append(validate_imsi)

    @classmethod
    def to_mongo(cls, value):
        """Convert value for storage."""

        try:
            return value.to_str()
        except ValueError:
            msg = '%r is not a valid IMSI.' % value
            raise ValidationError(msg)

    @classmethod
    def to_python(cls, value):
        """Convert value back to Python."""

        try:

            if isinstance(value, IMSI):
                value = value.to_str()

            return IMSI(value)

        except ValueError:
            msg = '%r is not a valid IMSI.' % value
            raise ValidationError(msg)
