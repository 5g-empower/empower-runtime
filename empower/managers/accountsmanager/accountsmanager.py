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

"""Accounts manager."""

from empower.core.service import EService
from empower.managers.accountsmanager.account import Account
from empower.managers.accountsmanager.accountshandler import AccountsHandler


class AccountsManager(EService):
    """Accounts manager."""

    HANDLERS = [AccountsHandler]

    accounts = {}

    def start(self):
        """Start accounts manager."""

        super().start()

        for account in Account.objects.all():
            self.accounts[account.username] = account

        if "root" not in self.accounts:

            self.log.info("No root user found, creating defaults!")

            self.create(username="root",
                        password="root",
                        name="admin",
                        email="admin@5g-empower.io")

            self.create(username="foo",
                        password="foo",
                        name="Foo",
                        email="foo@5g-empower.io")

            self.create(username="bar",
                        password="bar",
                        name="Bar",
                        email="bar@5g-empower.io")

    def check_permission(self, username, password):
        """Check if username/password match."""

        if username not in self.accounts:
            return False

        if self.accounts[username].password != password:
            return False

        return True

    def create(self, username, name, email, password):
        """Create new account."""

        if username in self.accounts:
            raise ValueError("Duplicate username %s found" % username)

        user = Account(username=username,
                       password=password,
                       name=name,
                       email=email)

        user.save()

        self.accounts[username] = user

        return self.accounts[username]

    def update(self, username, name, email, password=None):
        """Update account."""

        if username not in self.accounts:
            raise KeyError("Username %s not found" % username)

        user = self.accounts[username]

        try:
            user.name = name
            user.email = email
            if password:
                user.password = password
            user.save()
        finally:
            user.refresh_from_db()

        return self.accounts[username]

    def remove(self, username):
        """Check if username/password match."""

        if username == "root":
            raise ValueError("The 'root' account cannot be removed")

        if username not in self.accounts:
            raise KeyError("Username %s not found" % username)

        user = self.accounts[username]

        user.delete()

        del self.accounts[username]


def launch(context, service_id):
    """ Initialize the module. """

    return AccountsManager(context=context, service_id=service_id)
