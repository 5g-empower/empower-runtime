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

"""LVAPP Handlers."""

import empower.managers.apimanager.apimanager as apimanager

from empower.core.etheraddress import EtherAddress


# pylint: disable=W0223
class WTPHandler(apimanager.EmpowerAPIHandler):
    """Handler for accessing WTPs."""

    URLS = [r"/api/v1/wtps/?",
            r"/api/v1/wtps/([a-zA-Z0-9:]*)/?"]

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List devices.

        Args:

            [0]: the device address (optional)

        Example URLs:

            GET /api/v1/wtps

            [
                {
                    "addr": "00:0D:B9:2F:56:64",
                    "blocks": {},
                    "connection": null,
                    "desc": "PC Engines ALIX 2D",
                    "last_seen": 0,
                    "last_seen_ts": "1970-01-01T01:00:00.000000Z",
                    "period": 0,
                    "state": "disconnected"
                }
            ]

            GET /api/v1/wtps/00:0D:B9:2F:56:64 (disconnected)

            {
                "addr": "00:0D:B9:2F:56:64",
                "blocks": {},
                "connection": null,
                "desc": "PC Engines ALIX 2D",
                "last_seen": 0,
                "last_seen_ts": "1970-01-01T01:00:00.000000Z",
                "period": 0,
                "state": "disconnected"
            }

            GET /api/v1/wtps/00:0D:B9:2F:56:64 (connected)

            {
                "addr": "00:0D:B9:30:3E:18",
                "blocks": {
                    "0": {
                        "addr": "00:0D:B9:30:3E:18",
                        "band": "HT20",
                        "channel": 36,
                        "ht_supports": [
                            0,
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15
                        ],
                        "hwaddr": "04:F0:21:09:F9:9E",
                        "supports": [
                            6,
                            9,
                            12,
                            18,
                            24,
                            36,
                            48,
                            54
                        ],
                        "tx_policies": {
                            "60:F4:45:D0:3B:FC": {
                                "addr": "60:F4:45:D0:3B:FC",
                                "ht_mcs": [
                                    0,
                                    1,
                                    2,
                                    3,
                                    4,
                                    5,
                                    6,
                                    7,
                                    8,
                                    9,
                                    10,
                                    11,
                                    12,
                                    13,
                                    14,
                                    15
                                ],
                                "max_amsdu_len": 3839,
                                "mcast": "legacy",
                                "mcs": [
                                    6.0,
                                    9.0,
                                    12.0,
                                    18.0,
                                    24.0,
                                    36.0,
                                    48.0,
                                    54.0
                                ],
                                "no_ack": false,
                                "rts_cts": 2436,
                                "ur_count": 3
                            }
                        }
                    },
                    "1": {
                        "addr": "00:0D:B9:30:3E:18",
                        "band": "HT20",
                        "channel": 6,
                        "ht_supports": [
                            0,
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15
                        ],
                        "hwaddr": "D4:CA:6D:14:C2:09",
                        "supports": [
                            1,
                            2,
                            5,
                            6,
                            9,
                            11,
                            12,
                            18,
                            24,
                            36,
                            48,
                            54
                        ],
                        "tx_policies": {}
                    }
                },
                "connection": {
                    "addr": [
                        "192.168.1.9",
                        46066
                    ]
                },
                "desc": "PC Engines ALIX 2D",
                "last_seen": 8560,
                "last_seen_ts": "2019-08-23T13:09:43.140533Z",
                "period": 0,
                "state": "online"
            }
        """

        return self.service.devices \
            if not args else self.service.devices[EtherAddress(args[0])]

    @apimanager.validate(returncode=201, min_args=0, max_args=0)
    def post(self, *args, **kwargs):
        """Add a new device.

        Request:

            version: protocol version (1.0)
            addr: the device address (mandatory)
            desc: a human readable description of the device (optional)

        Example URLs:

            POST /api/v1/wtps

            {
                "version":"1.0",
                "addr": "00:0D:B9:2F:56:64"
            }

            POST /api/v1/wtps

            {
                "version":"1.0",
                "addr": "00:0D:B9:2F:56:64",
                "desc": "D-Link DIR-401"
            }
        """

        device = self.service.create(**kwargs)

        self.set_header("Location", "/api/v1/wtps/%s" % device.addr)

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all devices.

        Args:

            [0]: the device address (mandatory)

        Example URLs:

            DELETE /api/v1/wtps
            DELETE /api/v1/wtps/00:0D:B9:2F:56:64
        """

        if args:
            self.service.remove(EtherAddress(args[0]))
        else:
            self.service.remove_all()
