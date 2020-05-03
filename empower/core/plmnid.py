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

from stdnum import numdb
from stdnum.util import clean, isdigits

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField

from empower.core.serialize import serializable_dict


@serializable_dict
class PLMNID:
    """Public land mobile network  identifier (PLMNID)."""

    def __init__(self, plmnid):

        plmnid = clean(plmnid, ' -').strip().upper()

        if not isdigits(plmnid):
            raise ValueError("Invalid PLMNID %s" % plmnid)

        if len(plmnid) not in (4, 5):
            raise ValueError("Invalid PLMNID length %s" % plmnid)

        if len(tuple(numdb.get('imsi').split(plmnid))) < 2:
            raise ValueError("Invalid PLMNID format %s" % plmnid)

        self.info = dict(plmnid=plmnid)

        mcc_info, mnc_info = numdb.get('imsi').info(plmnid)

        self.info['mcc'] = mcc_info[0]
        self.info.update(mcc_info[1])
        self.info['mnc'] = mnc_info[0]
        self.info.update(mnc_info[1])

    @property
    def mcc(self):
        """Get mcc."""

        return self.info['mcc']

    @property
    def mnc(self):
        """Get mnc."""

        return self.info['mnc']

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "%s%s" % (self.mcc, self.mnc)

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
        if isinstance(other, PLMNID):
            return self.to_str() == other.to_str()
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
                    value = value.to_str()

                return PLMNID(value)

            except ValueError:
                msg = '%r is not a valid PLMNID.' % value
                raise ValidationError(msg)

        self.validators.append(validate_plmnid)

    @classmethod
    def to_mongo(cls, value):
        """Convert value for storage."""

        try:
            return value.to_str()
        except ValueError:
            msg = '%r is not a valid PLMNID.' % value
            raise ValidationError(msg)

    @classmethod
    def to_python(cls, value):
        """Convert value back to Python."""

        try:

            if isinstance(value, PLMNID):
                value = value.to_str()

            return PLMNID(value)

        except ValueError:
            msg = '%r is not a valid PLMNID.' % value
            raise ValidationError(msg)
