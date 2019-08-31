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

"""Applications unit tests."""

import json
import unittest
import requests

from .common import BaseTest
from .common import URL


class TestApplications(BaseTest):
    """Applications unit tests."""

    def test_register_new_app(self):
        """test_register_new_app."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER"
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps"), 200)

        data = {
            "name": "empower.tutorials.events.events",
        }

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

    def test_register_existing_app(self):
        """test_register_existing_app."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER"
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps"), 200)

        data = {
            "name": "empower.tutorials.events.events",
            "params": {}
        }

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        data = {
            "name": "empower.tutorials.events.events",
            "params": {}
        }

        params = ("root", "root", loc)
        self.post(params, data, 400)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

    def test_register_existing_app_invalid_creds(self):
        """test_register_existing_app_invalid_creds."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER"
            }
        }

        params = \
            ("foo", "foo", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 401)

        params = \
            ("root", "foo", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 401)

    def test_modify_app_invalid_param_name(self):
        """test_modify_app_invalid_param_name."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER"
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps"), 200)

        data = {
            "name": "empower.tutorials.events.events",
            "params": {}
        }

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        data = {
            "params": {
                "puppa": 2000
            }
        }

        params = ("root", "root", loc)
        self.put(params, data, 404)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

    def test_modify_app_param(self):
        """test_modify_app_param."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER"
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        data = {
            "name": "empower.apps.wifimobilitymanager.wifimobilitymanager"
        }

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        data = {
            "params": {
                "every": 5000
            }
        }

        params = ("root", "root", loc)
        self.put(params, data, 204)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

    def test_modify_app_invalid_param_value(self):
        """test_modify_app_invalid_param_value."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER"
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        data = {
            "name": "empower.apps.wifimobilitymanager.wifimobilitymanager"
        }

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        data = {
            "params": {
                "every": "puppa"
            }
        }

        params = ("root", "root", loc)
        self.put(params, data, 400)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)


if __name__ == '__main__':
    unittest.main()
