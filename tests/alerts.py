#!/usr/bin/env python3
#
# Copyright (c) 2022 Roberto Riggio
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

"""WTP unit tests."""

import json
import unittest
import requests

from .common import BaseTest
from .common import URL


class TestAlerts(BaseTest):
    """Alerts unit tests."""

    def test_create_new_alert(self):
        """test_create_new_alert."""

        data = {
            "message": "This is a new alert message"
        }
        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root", "/alerts"), 200)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada00"), 404)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873"), 400)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        req = requests.get(url=URL % params)
        alert = json.loads(req.text)
        self.assertEqual(alert['message'], "This is a new alert message")

        self.delete(("root", "root",
                     "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 404)

    def test_create_new_alert_empty_body(self):
        """test_create_new_alert_empty_body."""

        data = {}
        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root", "/alerts"), 200)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada00"), 404)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873"), 400)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        req = requests.get(url=URL % params)
        alert = json.loads(req.text)
        self.assertEqual(alert['message'], "Generic alert")

        self.delete(("root", "root",
                     "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 404)

    def test_update_alert(self):
        """test_update_alert."""

        data = {
            "message": "This is a new alert message"
        }
        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root", "/alerts"), 200)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada00"), 404)
        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873"), 400)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        req = requests.get(url=URL % params)
        alert = json.loads(req.text)
        self.assertEqual(alert['message'], "This is a new alert message")

        data = {
            "message": "This is the updated message"
        }
        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.put(params, data, 201)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        req = requests.get(url=URL % params)
        alert = json.loads(req.text)
        self.assertEqual(alert['message'], "This is the updated message")

        self.delete(("root", "root",
                     "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 404)

    def test_subscriptions(self):
        """test_subscriptions."""

        data = {
            "alert": "This is a new alert message"
        }
        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/subs/"
                  "foo")
        self.post(params, data, 400)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/subs/"
                  "00:0D:B9:2F:56:64")
        self.post(params, data, 201)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/subs/"
                  "00:0D:B9:2F:56:55")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/subs/"
                  "00:0D:B9:2F:56:55"), 200)

        self.delete(("root", "root",
                     "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/subs/"
                     "00:0D:B9:2F:56:55"), 204)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/subs/"
                  "00:0D:B9:2F:56:55"), 404)

        self.delete(("root", "root",
                     "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 404)

    def test_wtps(self):
        """test_wtps."""

        data = {
            "alert": "This is a new alert message"
        }
        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps/"
                  "foo")
        self.post(params, data, 400)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps/"
                  "00:0D:B9:2F:56:64")
        self.post(params, data, 201)

        params = ("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps/"
                  "00:0D:B9:2F:56:55")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps/"
                  "00:0D:B9:2F:56:55"), 200)

        self.delete(("root", "root",
                     "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps/"
                     "00:0D:B9:2F:56:55"), 204)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps/"
                  "00:0D:B9:2F:56:55"), 404)

        self.delete(("root", "root",
                     "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

        self.get(("root", "root",
                  "/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 404)


if __name__ == '__main__':
    unittest.main()
