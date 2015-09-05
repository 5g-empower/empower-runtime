#!/usr/bin/env python3
#
# Copyright (c) 2016, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""EmPOWER Account Class."""

from empower.persistence import Session
from empower.persistence.persistence import TblAccount

ROLE_ADMIN = "admin"
ROLE_USER = "user"


class Account(object):
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
