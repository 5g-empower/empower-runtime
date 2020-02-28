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

"""DataType."""

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField
from pymodm import validators


class LDataType:
    """LDataType."""
    DEFAULT_VALUE = None

    def __init__(self, data=None):        
        if data is None:
            # set to default
            self._value = self.DEFAULT_VALUE
        else:
            self._value = self._to_raw_(data)

    def _to_raw_(self, data):
        """ Converts data to int."""
        return int(data)
            
    def __index__(self):
        return self._value
    
    def __int__(self):
        return self._value

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._value == int(other):
                return True
        return False

    def __hash__(self):
        return self._value.__hash__()

    def __str__(self):
        """Return an ASCII representation of the object."""
        # The goal of __str__ is to be readable
        return str(self._value)

    def __repr__(self):
        # The goal of __repr__ is to be unambiguous
        # representation of python object 
        # usually eval will convert it back to that object
        return self.__class__.__name__ + "('" + str(self) + "')"

    def __setattr__(self, a, v):
        if hasattr(self, '_value'):
            raise TypeError("This object is immutable")
        object.__setattr__(self, a, v)


class LDataTypeField(MongoBaseField):
    """A field that stores LDataType."""    
    DATA_TYPE = LDataType

    def __init__(self, verbose_name=None, mongo_name=None, 
                min_value=None, max_value=None, **kwargs):
        """
        :parameters:
          - `verbose_name`: A human-readable name for the Field.
          - `mongo_name`: The name of this field when stored in MongoDB.
          - `min_value`: The minimum value that can be stored in this field.
          - `max_value`: The maximum value that can be stored in this field.
        .. seealso:: constructor for
                     :class:`~pymodm.base.fields.MongoBaseField`
        """

        super(LDataTypeField, self).__init__(verbose_name=verbose_name,
                                                mongo_name=mongo_name,
                                                **kwargs)

        def validate_ldatatype(value):

            try:
                self.DATA_TYPE(value)
            except ValueError:
                msg = '%r is not a valid %s.' % value, self.DATA_TYPE.__name__
                raise ValidationError(msg)

        self.validators.append(
            validators.together(
                validators.validator_for_func(int),
                validators.validator_for_min_max(min_value, max_value),
                validate_ldatatype))
                    
