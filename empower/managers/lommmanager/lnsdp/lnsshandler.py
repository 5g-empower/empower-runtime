#!/usr/bin/env python3
#
# Copyright (c) 2020 Fondazione Bruno Kessler
# Author(s): Cristina Costa (ccosta@fbk.eu)
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

"""LNS Handlers for the LNS Discovery Server."""

import empower.managers.apimanager.apimanager as apimanager

from empower.core.eui64 import EUI64


class LNSsHandler(apimanager.EmpowerAPIHandler):
    """REST API handler for managing LNSs."""

    URLS = [r"/api/v1/lnsd/lnss/?",
            r"/api/v1/lnsd/lnss/([a-zA-Z0-9:]*)/?"]

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List devices.

        Args:
            [0]: the lns euid (optional)

        Example URLs:

            GET /api/v1/lnsd/lnss

            [
                {
                    "euid": "0000:0000:0000:0001",
                    "desc": "Generic LNS",
                    "uri": "ws://0.0.0.0:6038/router-",
                    "lgtws": [
                        "b827:ebff:fee7:7681"
                    ],
                    "last_seen": 0,
                    "last_seen_ts": "1970-01-01T01:00:00.000000Z",
                    "period": 0
                }
            ]

            GET /api/v1/lnsd/lnss/::1

            {
                "euid": "0000:0000:0000:0001",
                "desc": "Generic LNS",
                "uri": "ws://0.0.0.0:6038/router-",
                "lgtws": [
                    "b827:ebff:fee7:7681"
                ],
                "last_seen": 0,
                "last_seen_ts": "1970-01-01T01:00:00.000000Z",
                "period": 0
            }

        """

        return self.service.lnss \
            if not args else self.service.lnss[EUI64(args[0])]

    @apimanager.validate(returncode=201, min_args=0, max_args=0)
    def post(self, *args, **kwargs):
        """Add a new LNS to the LNS Discovery Server Database.

        Request:

            version: protocol version (1.0)
            euid: the lns id in eui64 or euid format (mandatory)
            uri: the lns uri template (mandatory)
            desc: a human readable description of the device (optional)
            lgtws: the of lGTWS (optional)

        Example URLs:

            POST /api/v1/lnsd/lnss/"::1"

            {
                "version":"1.0",
                "euid": "0000:0000:0000:0001",
                "lgtws":["b827:ebff:fee7:7681"],
                "uri":"ws://0.0.0.0:6038/router-",
                "desc": "Generic LNS"
            }
        """

        kwargs['euid'] = EUI64(kwargs['euid'])

        lnss = self.service.add_lns(**kwargs)

        self.set_header("Location", "/api/v1/lnsd/lnss/%s" % lnss.euid)

    @apimanager.validate(returncode=204, min_args=1, max_args=1)
    def put(self, *args, **kwargs):
        """Add a new LNS to the LNS Discovery Server Database.

        Args:

            [0]: the lns id in eui64 or euid format (mandatory)

        Request:

            version: protocol version (1.0)
            uri: the lns uri template (mandatory)
            desc: a human readable description of the device (optional)
            lgtws: the of lGTWS (optional)

        Example URLs:

            PUT /api/v1/lnsd/lnss/::1

            {
                "version":"1.0",
                "lgtws":["b827:ebff:fee7:7681"],
                "uri":"ws://0.0.0.0:6038/router-",
                "desc": "Generic LNS"
            }
        """

        self.service.update_lns(euid=EUI64(args[0]), **kwargs)

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all devices.

        Args:
            [0]: the lns id in eui64 or euid format (optional)

        Example URLs:

            DELETE /api/v1/lnsd/lnss
            DELETE /api/v1/lnsd/lnss/::1
        """

        if args:
            self.service.remove_lns(EUI64(args[0]))
        else:
            self.service.remove_all_lnss()
