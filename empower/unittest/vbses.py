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

"""VBSes unit tests."""

import json
import unittest
import requests

from .common import BaseTest
from .common import URL


class TestVBSes(BaseTest):
    """VBSes unit tests."""

    def test_create_new_device_empty_body(self):
        """test_create_new_device_empty_body."""

        data = {}
        params = ("root", "root", "/vbses/00:15:6d:84:13:0f")
        self.post(params, data, 400)

    def test_create_new_device_wrong_address(self):
        """test_create_new_device_wrong_address."""

        data = {
            "addr": "AA:15:6d:84:13"
        }
        params = ("root", "root", "/vbses/00:15:6d:84:13:0f")
        self.post(params, data, 400)

    def test_create_new_device(self):
        """test_create_new_device."""

        data = {
            "addr": "AA:15:6d:84:13:0f"
        }
        params = ("root", "root", "/vbses")
        self.post(params, data, 201)

        self.get(("root", "root", "/vbses"), 200)
        self.get(("root", "root", "/vbses/AA:15:6d:84:13:0f"), 200)
        self.get(("root", "root", "/vbses/11:22:33:44:55:66"), 404)
        self.get(("root", "root", "/vbses/AA:15:6d:84:13"), 400)

        params = ("root", "root", "/vbses/AA:15:6d:84:13:0f")
        req = requests.get(url=URL % params)
        device = json.loads(req.text)
        self.assertEqual(device['desc'], "Generic device")

        self.delete(("root", "root", "/vbses/AA:15:6d:84:13:0f"), 204)

        self.get(("root", "root", "/vbses/AA:15:6d:84:13:0f"), 404)

    def test_create_new_device_custom_desc(self):
        """test_create_new_device_custom_desc."""

        data = {
            "addr": "AA:15:6d:84:13:0f",
            "desc": "Custom description"
        }
        params = ("root", "root", "/vbses")
        self.post(params, data, 201)

        self.get(("root", "root", "/vbses"), 200)
        self.get(("root", "root", "/vbses/AA:15:6d:84:13:0f"), 200)
        self.get(("root", "root", "/vbses/11:22:33:44:55:66"), 404)
        self.get(("root", "root", "/vbses/AA:15:6d:84:13"), 400)

        params = ("root", "root", "/vbses/AA:15:6d:84:13:0f")
        req = requests.get(url=URL % params)
        device = json.loads(req.text)
        self.assertEqual(device['desc'], "Custom description")

        self.delete(("root", "root", "/vbses/AA:15:6d:84:13:0f"), 204)

        self.get(("root", "root", "/vbses/AA:15:6d:84:13:0f"), 404)


if __name__ == '__main__':
    unittest.main()
