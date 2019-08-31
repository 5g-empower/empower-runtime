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

"""Exposes a RESTful interface ."""

import empower.managers.apimanager.apimanager as apimanager


# pylint: disable=W0223
class AccountsHandler(apimanager.EmpowerAPIHandler):
    """All the accounts defined in the controller."""

    URLS = [r"/api/v1/accounts/?",
            r"/api/v1/accounts/([a-zA-Z0-9:.]*)/?"]

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List the accounts.

        Args:

            [0]: the username

        Example URLs:

            GET /api/v1/accounts

            [
                {
                    "email": "admin@empower.it",
                    "name": "admin",
                    "username": "root"
                },
                {
                    "email": "foo@empower.it",
                    "name": "Foo",
                    "username": "foo"
                },
                {
                    "email": "bar@empower.it",
                    "name": "Bar",
                    "username": "bar"
                }
            ]

            GET /api/v1/accounts/root

            {
                "email": "admin@empower.it",
                "name": "admin",
                "username": "root"
            }
        """

        return self.service.accounts \
            if not args else self.service.accounts[args[0]]

    @apimanager.validate(returncode=201)
    def post(self, *args, **kwargs):
        """Create a new account.

        Request:

            version: protocol version (1.0)
            username: username (mandatory)
            password: password (mandatory)
            name: name (mandatory)
            email: email (mandatory)

        Example URLs:

            POST /api/v1/accounts

            {
              "version" : 1.0,
              "username" : "foo",
              "password" : "foo",
              "name" : "foo",
              "email" : "foo@empower.io"
            }
        """

        self.service.create(username=kwargs['username'],
                            password=kwargs['password'],
                            name=kwargs['name'],
                            email=kwargs['email'])

    @apimanager.validate(returncode=204, min_args=1, max_args=1)
    def put(self, *args, **kwargs):
        """Update an account.

        Args:

            [0]: the username

        Request:

            version: protocol version (1.0)
            name: name (optional)
            email: email (optional)
            password: password (optional)
            new_password: new_password (optional)
            new_password_confirm: new_password_confirm (optional)

        Example URLs:

            PUT /api/v1/accounts/test

            {
              "version" : 1.0,
              "name" : "foo",
              "email" : "foo@empowr.io",
              "password" : "foo",
              "new_password" : "new",
              "new_password_confirm" : "new",
            }

            PUT /api/v1/accounts/test

            {
              "version" : 1.0
              "email" : "new@empowr.io",
            }
        """

        kwargs['username'] = args[0]

        if 'new_password' in kwargs and 'new_password_confirm' in kwargs:

            if kwargs['new_password'] != kwargs['new_password_confirm']:
                raise ValueError("Passwords do not match")

            kwargs['password'] = kwargs['new_password']

            del kwargs['new_password']
            del kwargs['new_password_confirm']

        self.service.update(**kwargs)

    @apimanager.validate(returncode=204, min_args=1, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete an account.

        Args:

            [0]: the username

        Example URLs:

            DELETE /api/v1/accounts/foo
        """

        self.service.remove(args[0])
