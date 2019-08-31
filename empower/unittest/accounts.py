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

"""Accounts unit tests."""

import json
import unittest
import requests

from .common import BaseTest
from .common import URL


class TestAccounts(BaseTest):
    """Accounts unit tests."""

    def test_simple_gets(self):
        """test_simple_gets."""

        self.get(("root", "root", "/accounts"), 200)
        self.get(("root", "root", "/accounts/root"), 200)
        self.get(("root", "root", "/accounts/foo"), 200)
        self.get(("root", "root", "/accounts/bar"), 200)
        self.get(("foo", "foo", "/accounts"), 200)
        self.get(("foo", "foo", "/accounts/root"), 200)
        self.get(("foo", "foo", "/accounts/foo"), 200)
        self.get(("foo", "foo", "/accounts/bar"), 200)

    def test_create_existing_user(self):
        """test_create_existing_user."""

        data = {
            "username": "foo",
            "password": "foo",
            "name": "foo",
            "email": "foo@empower.io"
        }

        self.post(("root", "root", "/accounts"), data, 400)

    def test_create_new_user(self):
        """test_create_new_user."""

        data = {
            "username": "dummy",
            "password": "dummy",
            "name": "dummy",
            "email": "dummy@empower.io"
        }

        self.post(("root", "root", "/accounts"), data, 201)
        self.get(("root", "root", "/accounts/dummy"), 200)
        self.delete(("root", "root", "/accounts/dummy"), 204)
        self.get(("root", "root", "/accounts/dummy"), 404)

    def test_update_user_details(self):
        """test_update_user_details."""

        data = {
            "username": "dummy",
            "password": "dummy",
            "name": "dummy",
            "email": "dummy@empower.io"
        }

        self.post(("root", "root", "/accounts"), data, 201)

        data = {}
        self.put(("root", "root", "/accounts/dummy"), data, 204)

        data = {
            "username": "dummydummy"
        }

        self.put(("root", "root", "/accounts/dummy"), data, 204)

        data = {
            "username": "dummy",
            "password": "dummy",
            "name": "Roberto Riggio",
            "email": "dummy@empower.io"
        }

        self.put(("root", "root", "/accounts/dummy"), data, 204)

        req = requests.get(url=URL % ("root", "root", "/accounts/dummy"))
        user = json.loads(req.text)
        self.assertEqual(user['name'], "Roberto Riggio")

        self.delete(("root", "root", "/accounts/dummy"), 204)
        self.get(("root", "root", "/accounts/dummy"), 404)

    def test_credentials(self):
        """test_credentials."""

        data = {
            "username": "dummy",
            "password": "dummy",
            "name": "dummy",
            "email": "dummy@empower.io"
        }

        self.post(("foo", "foo", "/accounts"), data, 401)

        self.post(("root", "foo", "/accounts"), data, 401)

        self.post(("root", "root", "/accounts"), data, 201)

        data = {
            "new_password": "ciccio",
            "new_password_confirm": "ciccio"
        }

        self.put(("dummy", "dummy", "/accounts/dummy"), data, 204)

        data = {
            "version": "1.0",
            "new_password": "dummy",
            "new_password_confirm": "dummy"
        }

        self.put(("dummy", "dummy", "/accounts/dummy"), data, 401)

        self.put(("dummy", "ciccio", "/accounts/dummy"), data, 204)

        self.put(("foo", "foo", "/accounts/dummy"), data, 401)

        self.put(("root", "root", "/accounts/dummy"), data, 204)


if __name__ == '__main__':
    unittest.main()
