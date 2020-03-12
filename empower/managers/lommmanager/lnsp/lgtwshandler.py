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
"""LoRaWAN GTWs Handlers."""

import empower.managers.apimanager.apimanager as apimanager

from empower.core.eui64 import EUI64


class LGTWsHandler(apimanager.EmpowerAPIHandler):
    """REST API handler for managing LoRaWAN GTWs."""

    URLS = [r"/api/v1/lns/lgtws/?",
            r"/api/v1/lns/lgtws/([a-zA-Z0-9: ]*)/?"]

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List LoRaWAN Gateways.

        Args:
            [0]: the LoRaWAN Gateway EUID (optional)

        Example URLs:
            GET /api/v1/lns/lgtws
            [
                {"lgtw_euid": "b8:27:eb:ff:fe:e7:76:81",
                "desc": "iC880A Concentrator",
                "state": "disconnected",
                "owner": "00:00:00:00:00:00:00:00",
                "lgtw_version": [...],
                "lgtw_config": [...],
                "last_seen": "2020-02-18 12:40:52",
                "last_seen_ts": 1582026052.0,
                "connection": null},
                {[...]},
            ]

            GET /api/v1/lns/lgtws/b8:27:eb:ff:fe:e7:76:81
                {
                "lgtw_euid": "b8:27:eb:ff:fe:e7:76:81",
                "desc": "iC880A Concentrator",
                "state": "disconnected",
                "owner": "00:00:00:00:00:00:00:00",
                "lgtw_version": [...],
                "lgtw_config": [...],
                "last_seen": "2020-02-18 12:40:52",
                "last_seen_ts": 1582026052.0,
                "connection": null
                }
        """
        out = []
        desc = self.get_argument("desc", None)
        name = self.get_argument("name", None)

        if len(args) == 1:
            lgtw_euid = EUI64(args[0])

            if lgtw_euid in self.service.lgtws:
                lgtw = self.service.lgtws[lgtw_euid].to_dict()
                if not ((desc and (desc not in lgtw["desc"])) or
                        (name and (name not in lgtw["name"]))):
                    out = [lgtw]
            return out

        for key in self.service.lgtws:
            if (desc and
                    desc not in self.service.lgtws[key].to_dict()["desc"]):
                continue
            if (name and
                    name not in self.service.lgtws[key].to_dict()["name"]):
                continue
            out.append(self.service.lgtws[key].to_dict())
        return out

    @apimanager.validate(returncode=201, min_args=1, max_args=1)
    def post(self, *args, **kwargs):
        """Add a new LoRaWAN end device.

        Args:
            [0]: the LoRaWAN end EUI (mandatory)

        Request:
            version: protocol version (1.0)
            desc: a human readable description of the device (optional)

        Example URLs:
            POST /api/v1/lns/lgtws/b8:27:eb:ff:fe:e7:76:81
            {
                "version":"1.0",
                "desc": "LoRaWAN GTW iC880A"
            }
        """
        lgtw = self.service.add_lgtw(args[0], **kwargs)
        self.set_header("Location", "/api/v1/lns/lgtw/%s" % lgtw.lgtw_euid)

    @apimanager.validate(returncode=201, min_args=1, max_args=4)
    def put(self, *args, **kwargs):
        """Add a new LoRaWAN end device.

        Args:
            [0]: the LoRaWAN Gateway euid (mandatory)

        Request:
            version: protocol version (1.0)
            desc: a human readable description of the device (optional)

        Example URLs:
            PUT /api/v1/lns/lgtws/b8:27:eb:ff:fe:e7:76:81
            {
                "version":"1.0",
                "lgtw_euid": "b8:27:eb:ff:fe:e7:76:81",
                "desc": "LoRaWAN GTW iC880A"
            }
        """
        lgtw = self.service.update_lgtw(args[0], **kwargs)
        self.set_header("Location", "/api/v1/lns/lgtws/%s" % lgtw.lgtw_euid)

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all LoRaWAN end devices.

        Args:
            [0]: the lGTW euid

        Example URLs:
            DELETE /api/v1/lns/lgtws
            DELETE /api/v1/lns/lgtws/08:27:eb:ff:fe:e7:76:91
        """
        if args:
            self.service.remove_lgtw(EUI64(args[0]))
        else:
            self.service.remove_all_lgtws()
