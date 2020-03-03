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

# TODO ADD REFERENCE TO ALLOWED DEVICES

import empower.managers.apimanager.apimanager as apimanager

from empower.core.eui64 import EUI64

class LGTWsHandler(apimanager.EmpowerAPIHandler):
    """Handler for accessing LoRaWAN GTWs."""

    URLS = [r"/api/v1/lns/lgtws/?",
            r"/api/v1/lns/lgtws/([a-zA-Z0-9:]*)/?"]

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
        if len(args) == 0:
            desc = self.get_argument("desc",None)
            out  = []
            for key in self.service.lgtws:
                if desc and desc not in self.service.lgtws[key].to_dict()["desc"]:
                    continue
                out.append(self.service.lgtws[key].to_dict())
            return out
        else:
            try:
                lgtw_euid = EUI64(args[0]).eui
            except ValueError  as err:
                self.set_status(400)
                self.finish({"status_code":400,"title":"lgtw_id wrong format","detail":str(err)})

            if lgtw_euid in self.service.lgtws:
                return [self.service.lgtws[lgtw_euid].to_dict()]
            else:
                return []

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
        try:
            print(args[0])
            print(kwargs)
            lgtw = self.service.add_lgtw(args[0], **kwargs)
        except:
            raise
        else:
            self.set_header("Location", "/api/v1/lns/lgtw/%s" % lgtw.lgtw_euid)

    @apimanager.validate(returncode=201, min_args=1, max_args=1)
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
        try:
            lgtw = self.service.update_lgtw(args[0], **kwargs)
        except:
            raise
        else:
            self.set_header("Location", "/api/v1/lns/lgtw/%s" % lgtw.lgtw_euid)

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
            self.service.remove_lgtw(EUI64(args[0]).eui)
        else:
            self.service.remove_all_lgtws()
