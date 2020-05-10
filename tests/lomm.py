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

"""LOMM unit tests."""

import json
import unittest
import requests

from .common import BaseTest
from .common import URL


class TestLOMM(BaseTest):
    """LOMM unit tests."""

    def test_create_new_lns_wrong_euid(self):
        """test_create_new_lns."""

        data = {
            "version": "1.0",
            "euid": "0001",
            "lgtws": ["b827:ebff:fee7:7681"],
            "uri": "ws://0.0.0.0:6038/router-",
            "desc": "Generic LNS"
        }

        params = ("root", "root", "/lnsd/lnss")

        self.post(params, data, 400)

    def test_create_new_lns_missing_euid(self):
        """test_create_new_lns."""

        data = {
            "version": "1.0",
            "lgtws": ["b827:ebff:fee7:7681"],
            "uri": "ws://0.0.0.0:6038/router-",
            "desc": "Generic LNS"
        }

        params = ("root", "root", "/lnsd/lnss")

        self.post(params, data, 404)

    def test_create_new_lns(self):
        """test_create_new_lns."""

        data = {
            "version": "1.0",
            "euid": "0000:0000:0000:0001",
            "lgtws": ["b827:ebff:fee7:7681"],
            "uri": "ws://0.0.0.0:6038/router-",
            "desc": "Generic LNS"
        }

        params = ("root", "root", "/lnsd/lnss")

        self.post(params, data, 201)

        self.get(("root", "root", "/lnsd/lnss"), 200)
        self.get(("root", "root", "/lnsd/lnss/::1"), 200)
        self.get(("root", "root", "/lnsd/lnss/::2"), 404)
        self.get(("root", "root", "/lnsd/lnss/0001"), 400)

        params = ("root", "root", "/lnsd/lnss/::1")
        req = requests.get(url=URL % params)
        device = json.loads(req.text)
        self.assertEqual(device['desc'], "Generic LNS")

        data = {
            "version": "1.0",
            "lgtws": ["b827:ebff:fee7:7681"],
            "uri": "ws://0.0.0.0:6038/router-",
            "desc": "Modified LNS"
        }

        params = ("root", "root", "/lnsd/lnss/::1")

        self.put(params, data, 204)

        params = ("root", "root", "/lnsd/lnss/::1")
        req = requests.get(url=URL % params)
        device = json.loads(req.text)
        self.assertEqual(device['desc'], "Modified LNS")

        self.delete(("root", "root", "/lnsd/lnss/::1"), 204)

        self.get(("root", "root", "/lnsd/lnss/::1"), 404)

    def test_create_new_lgtw(self):
        """test_create_new_lgtw."""

        data = {
            "version": "1.0",
            "euid": "0000:0000:0000:0001",
            "lgtws": ["b827:ebff:fee7:7681"],
            "uri": "ws://0.0.0.0:6038/router-",
            "desc": "Generic LNS"
        }

        params = ("root", "root", "/lnsd/lnss")

        self.post(params, data, 201)

        self.get(("root", "root", "/lnsd/lnss"), 200)
        self.get(("root", "root", "/lnsd/lnss/::1"), 200)
        self.get(("root", "root", "/lnsd/lnss/::2"), 404)
        self.get(("root", "root", "/lnsd/lnss/0001"), 400)

        params = ("root", "root", "/lnsd/lnss/::1/lgtws/b827:ebff:fee7:7681")
        self.post(params, data, 201)

        params = ("root", "root", "/lnsd/lnss/::1/lgtws/b827:ebff:fee7:7682")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/lnsd/lnss/::1/lgtws/b827:ebff:fee7:7681"), 200)

        params = ("root", "root", "/lnsd/lnss/::1/lgtws/b827:ebff:fee7:7682")
        self.delete(params, 204)

        self.get(("root", "root",
                  "/lnsd/lnss/::1/lgtws/b827:ebff:fee7:7682"), 404)

        self.delete(("root", "root", "/lnsd/lnss/::1"), 204)

        self.get(("root", "root", "/lnsd/lnss/::1"), 404)


if __name__ == '__main__':
    unittest.main()
