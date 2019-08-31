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

"""Base-class for unit Tests."""

import json
import unittest
import requests

URL = "http://%s:%s@127.0.0.1:8888/api/v1%s"


class BaseTest(unittest.TestCase):
    """Base-class for unit Tests."""

    def setUp(self):
        """Delete test entries."""

        requests.delete(url=URL % ("root", "root", "/projects"))

        requests.delete(url=URL % ("root", "root", "/accounts/dummy"))

        requests.delete(url=URL % ("root", "root", "/wtps"))

        requests.delete(url=URL % ("root", "root", "/vbses"))

    def get(self, params, result):
        """REST get method."""

        req = requests.get(url=URL % params)
        self.assertEqual(req.status_code, result, req.text)
        return req

    def post(self, params, data, result):
        """Test post method."""

        data["version"] = "1.0"
        req = requests.post(url=URL % params, data=json.dumps(data))
        self.assertEqual(req.status_code, result, req.text)
        return req

    def put(self, params, data, result):
        """Test put method."""

        data["version"] = "1.0"
        req = requests.put(url=URL % params, data=json.dumps(data))
        self.assertEqual(req.status_code, result, req.text)

    def delete(self, params, result):
        """REST delete method."""

        req = requests.delete(url=URL % params)
        self.assertEqual(req.status_code, result, req.text)
