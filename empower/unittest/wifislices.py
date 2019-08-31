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

"""Wi-Fi slices unit tests."""

import json
import unittest
import requests

from .common import BaseTest
from .common import URL


class TestWiFiSlices(BaseTest):
    """Wi-Fi slices unit tests."""

    def test_create_new_wifi_slice(self):
        """test_create_new_wifi_slice."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f",
                    "04:46:65:49:e0:11",
                    "04:46:65:49:e0:11"
                ]
            },
            "wifi_slices": [
                {
                    "slice_id": 82,
                    "properties": {
                        "amsdu_aggregation": "false",
                        "quantum": 10000,
                        "sta_scheduler": 1
                    },
                    "devices": {
                        "11:22:33:44:55:66": {
                            "amsdu_aggregation": "true",
                            "quantum": 1000,
                            "sta_scheduler": 0
                        }
                    }
                }
            ]
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("foo", "foo",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("bar", "bar",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lte_slices")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/0")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lte_slices/0")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lte_slices/82")
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.delete(params, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.get(params, 404)

    def test_create_new_wifi_slice_after_prj(self):
        """test_create_new_wifi_slice_after_prj."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f",
                    "04:46:65:49:e0:11",
                    "04:46:65:49:e0:11"
                ]
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("foo", "foo",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("bar", "bar",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lte_slices")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/0")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lte_slices/0")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lte_slices/82")
        self.get(params, 404)

        data = {
            "slice_id": 82,
            "properties": {
                "amsdu_aggregation": "false",
                "quantum": 10000,
                "sta_scheduler": 1
            },
            "devices": {
                "11:22:33:44:55:66": {
                    "amsdu_aggregation": "true",
                    "quantum": 1000,
                    "sta_scheduler": 0
                }
            }
        }

        params = ("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices")
        self.post(params, data, 201)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lte_slices/82")
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.delete(params, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.get(params, 404)

    def test_update_wifi_slice(self):
        """test_update_wifi_slice."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f",
                    "04:46:65:49:e0:11",
                    "04:46:65:49:e0:11"
                ]
            },
            "wifi_slices": [
                {
                    "slice_id": 82,
                    "properties": {
                        "amsdu_aggregation": "false",
                        "quantum": 10000,
                        "sta_scheduler": 1
                    },
                    "devices": {
                        "11:22:33:44:55:66": {
                            "amsdu_aggregation": "true",
                            "quantum": 1000,
                            "sta_scheduler": 0
                        }
                    }
                }
            ]
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.get(params, 200)

        data = {
            "properties": {
                "amsdu_aggregation": "false",
                "quantum": 9000,
                "sta_scheduler": 0
            }
        }

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.put(params, data, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        req = requests.get(url=URL % params)
        slc = json.loads(req.text)
        self.assertEqual(slc['properties']['quantum'], 9000)

        data = {
            "properties": {
                "amsdu_aggregation": "false",
                "quantum": 9000,
                "sta_scheduler": 0
            },
            "devices": {
                "aa:bb:cc:dd:ee:ff": {
                    "amsdu_aggregation": "false",
                    "quantum": 3000,
                    "sta_scheduler": 0
                }
            }
        }

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.put(params, data, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        req = requests.get(url=URL % params)
        slc = json.loads(req.text)
        self.assertEqual(slc['devices']['AA:BB:CC:DD:EE:FF']['quantum'], 3000)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.delete(params, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/82")
        self.get(params, 404)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.get(params, 404)

    def test_delete_default_wifi_slice(self):
        """test_delete_default_wifi_slice."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f",
                    "04:46:65:49:e0:11",
                    "04:46:65:49:e0:11"
                ]
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/0")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/0")
        self.delete(params, 400)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wifi_slices/0")
        self.get(params, 200)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.delete(params, 204)

        params = \
            ("root", "root",
             "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.get(params, 404)


if __name__ == '__main__':
    unittest.main()
