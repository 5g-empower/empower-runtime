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

"""Account Class."""

from pymodm import MongoModel, fields


class Account(MongoModel):
    """An user account on this controller."""

    username = fields.CharField(primary_key=True)
    password = fields.CharField(required=True)
    name = fields.CharField(required=True)
    email = fields.EmailField(required=True)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        return {'username': self.username,
                'name': self.name,
                'email': self.email}

    def to_str(self):
        """Return an ASCII representation of the object."""

        return str(self.username)

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.username)

    def __eq__(self, other):
        if isinstance(other, Account):
            return self.username == other.username
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
