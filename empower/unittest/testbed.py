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

"""Testbed configuration unit tests."""


import unittest

from .common import BaseTest


class TestTestbed(BaseTest):
    """Projects unit tests."""

    def test_create_project(self):
        """test_create_project"""

        data = {
            "owner": "foo",
            "desc": "EmPOWER Guests",
            "wifi_props": {
                "ssid": "EmPOWER Guests",
                "allowed": {
                    "60:57:18:b1:a4:b8": {
                        "addr": "60:57:18:b1:a4:b8",
                        "desc": "Dell Laptop"
                    },
                    "18:5e:0f:e3:b8:68": {
                        "addr": "18:5e:0f:e3:b8:68",
                        "desc": "Dell Laptop"
                    },
                    "60:f4:45:d0:3b:fc": {
                        "addr": "60:83:73:03:83:A3",
                        "desc": "Roberto's iPhone"
                    }
                }
            },
            "wifi_slices": [
                {
                    "slice_id": 56,
                    "properties": {
                        "amsdu_aggregation": "false",
                        "quantum": 10000,
                        "sta_scheduler": 1
                    }
                }
            ]
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        data = {
            "owner": "foo",
            "desc": "EmPOWER Mcast",
            "wifi_props": {
                "ssid": "EmPOWER Mcast",
                "bssid_type": "shared",
                "allowed": {
                    "60:57:18:b1:a4:b8": {
                        "addr": "60:57:18:b1:a4:b8",
                        "desc": "Dell Laptop"
                    },
                    "18:5e:0f:e3:b8:68": {
                        "addr": "18:5e:0f:e3:b8:68",
                        "desc": "Dell Laptop"
                    },
                    "60:f4:45:d0:3b:fc": {
                        "addr": "60:f4:45:d0:3b:fc",
                        "desc": "Roberto's iPhone"
                    }
                }
            },
            "wifi_slices": [
                {
                    "slice_id": 56,
                    "properties": {
                        "amsdu_aggregation": "false",
                        "quantum": 10000,
                        "sta_scheduler": 1
                    }
                }
            ]
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada36")
        self.post(params, data, 201)

        # VBSes
        vbses = [
            ("00:00:00:00:00:01", "Ettus B210")
        ]
        for vbs in vbses:
            data = {"addr": vbs[0], "desc": vbs[1]}
            params = ("root", "root", "/vbses")
            self.post(params, data, 201)

        # ALIX APUs
        wtps = [
            ("00:0D:B9:54:3B:DC", "PC Engines APU2 (1)"),
            ("00:0D:B9:54:3D:00", "PC Engines APU2 (2)"),
            ("00:0D:B9:54:3D:20", "PC Engines APU2 (3)"),
            ("00:0D:B9:54:3C:CC", "PC Engines APU2 (4)"),
            ("00:0D:B9:54:27:F8", "PC Engines APU2 (5)"),
            ("00:0D:B9:54:3C:F4", "PC Engines APU2 (6)")
        ]
        for wtp in wtps:
            data = {"addr": wtp[0], "desc": wtp[1]}
            params = ("root", "root", "/wtps")
            self.post(params, data, 201)


if __name__ == '__main__':
    unittest.main()
