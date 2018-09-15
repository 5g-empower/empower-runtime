#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""EmPOWER Account Class."""

from empower.persistence import Session
from empower.persistence.persistence import TblAccount

ROLE_ADMIN = "admin"
ROLE_USER = "user"


class Account:
    """An user account on this controller."""

    def __init__(self, username, password, name, surname, email, role):
        self._username = username
        self._password = password
        self._role = role
        self._name = name
        self._surname = surname
        self._email = email

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        return {'username': self.username,
                'role': self.role,
                'name': self.name,
                'surname': self.surname,
                'email': self.email}

    @property
    def username(self):
        """Get username."""
        return self._username

    @property
    def password(self):
        """Get password"""
        return self._password

    @property
    def role(self):
        """Get role."""
        return self._role

    @property
    def name(self):
        """Get name."""
        return self._name

    @property
    def surname(self):
        """Get surname."""
        return self._surname

    @property
    def email(self):
        """Get email."""
        return self._email

    @password.setter
    def password(self, password):
        """Set name."""

        session = Session()
        account = session.query(TblAccount) \
                         .filter(TblAccount.username == self.username) \
                         .first()
        account.password = password
        session.commit()
        self._password = password

    @name.setter
    def name(self, name):
        """Set name."""

        session = Session()
        account = session.query(TblAccount) \
                         .filter(TblAccount.username == self.username) \
                         .first()
        account.name = name
        session.commit()
        self._name = name

    @surname.setter
    def surname(self, surname):
        """Set surname."""

        session = Session()
        account = Session().query(TblAccount) \
                           .filter(TblAccount.username == self.username) \
                           .first()
        account.surname = surname
        session.commit()
        self._surname = surname

    @email.setter
    def email(self, email):
        """Set email."""

        session = Session()
        account = Session().query(TblAccount) \
                           .filter(TblAccount.username == self.username) \
                           .first()
        account.email = email
        session.commit()
        self._email = email

    def __str__(self):
        return str(self.username)

    def __hash__(self):
        return hash(self.username)

    def __eq__(self, other):
        if isinstance(other, Account):
            return self.username == other.username
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
