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
            "desc": "5G-EmPOWER Wi-Fi Network",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "60:57:18:b1:a4:b8",
                    "18:5e:0f:e3:b8:68",
                    "60:f4:45:d0:3b:fc"
                ]
            },
            "wifi_slices": [
                {
                    "slice_id": 80,
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
            "desc": "5G-EmPOWER Wi-Fi Network (Shared)",
            "wifi_props": {
                "ssid": "SharedEmPOWER",
                "bssid_type": "shared",
                "allowed": [
                    "60:57:18:b1:a4:b8",
                    "18:5e:0f:e3:b8:68",
                    "60:f4:45:d0:3b:fc",
                    "18:5e:0f:e3:b8:45"
                ]
            },
            "wifi_slices": [
                {
                    "slice_id": 80,
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
        addrs = ["00:00:00:00:00:01"]
        for addr in addrs:
            data = {"addr": addr, "desc": "Ettus B210"}
            params = ("root", "root", "/vbses")
            self.post(params, data, 201)

        # ALIX 2C
        addrs = ["00:0D:B9:2F:56:64", "00:0D:B9:2F:56:58", "00:0D:B9:2F:56:5C",
                 "00:0D:B9:2F:56:B4", "00:0D:B9:2F:55:CC", "00:0D:B9:2F:63:78",
                 "00:0D:B9:30:3E:04", "00:0D:B9:30:3E:18", "00:0D:B9:2F:56:BC",
                 "00:0D:B9:2F:56:48"]
        for addr in addrs:
            data = {"addr": addr, "desc": "PC Engines ALIX 2D"}
            params = ("root", "root", "/wtps")
            self.post(params, data, 201)

        # ALIX 2C
        addrs = ["00:0D:B9:2F:56:64", "00:0D:B9:2F:56:58", "00:0D:B9:2F:56:5C",
                 "00:0D:B9:2F:56:B4", "00:0D:B9:2F:55:CC", "00:0D:B9:2F:63:78",
                 "00:0D:B9:30:3E:04", "00:0D:B9:30:3E:18", "00:0D:B9:2F:56:BC",
                 "00:0D:B9:2F:56:48"]
        for addr in addrs:
            data = {"addr": addr, "desc": "PC Engines ALIX 2D"}
            params = ("root", "root", "/wtps")
            self.post(params, data, 201)

        # WDR4300
        data = {"addr": "60:E3:27:B8:35:A5", "desc": "TP-Link WDR4300"}
        params = ("root", "root", "/wtps")
        self.post(params, data, 201)

        # WNDR4300
        data = {"addr": "60:E3:27:B8:35:A5", "desc": "Netgear WNDR 4300"}
        params = ("root", "root", "/wtps")
        self.post(params, data, 201)

        # WNDR4300
        data = {"addr": "C0:A0:BB:ED:84:81", "desc": "D-Link DIR505"}
        params = ("root", "root", "/wtps")
        self.post(params, data, 201)

        data = {"addr": "C0:A0:BB:ED:86:77", "desc": "D-Link DIR505"}
        params = ("root", "root", "/wtps")
        self.post(params, data, 201)


if __name__ == '__main__':
    unittest.main()
