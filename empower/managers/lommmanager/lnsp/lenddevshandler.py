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
"""LoRaWAN End Device Handlers."""

import empower.managers.apimanager.apimanager as apimanager

from empower.core.eui64 import EUI64


class LEndDevsHandler(apimanager.EmpowerAPIHandler):
    """REST API handler for managing LoRaWAN End Devices."""

    URLS = [r"/api/v1/lns/lenddevs/?",
            r"/api/v1/lns/lenddevs/([a-zA-Z0-9:]*)/?"]

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List LoRaWAN End devices.

        Args:
            [0]: devEUI (optional)

        Example URLs:
            GET /api/v1/lns/lenddevs
            [
                {
                    "devEUI": "0028A154B89172D2"
                    "devAddr": "0028A154B89172D2",
                    "desc": "End Device XXX"
                }
            ]

            GET /api/v1/lns/lenddevs/00:28:A1:54:B8:91:72:D2
            {
                    "devAddr": "0028A154B89172D2",
                    "desc": "End Device XXX"
            }
        """
        if not args:
            out = []
            for key in self.service.lenddevs:
                out.append(self.service.lenddevs[key].to_dict())
            return out

        dev_eui = EUI64(args[0])
        print(self.service.lenddevs)
        return self.service.lenddevs[dev_eui].to_dict()

    @apimanager.validate(returncode=201, min_args=0, max_args=1)
    def post(self, *args, **kwargs):
        """Add a new LoRaWAN end device.

        Args:
            [0]: devEUI

        Request:
            version: protocol version (1.0)
            desc: a human readable description of the device (optional)

        Example URLs:
            POST /api/v1/lns/lenddevs/00:28:A1:54:B8:91:72:D2
            {
                "version":"1.0",
                "desc": "LoRaWAN End Device"
                "joinEUI": joinEUI
                "appKey": cryptographic application key
                "nwkKey": cryptographic network key
                "appSKey": cryptographic session application key
                "nwkSKey": cryptographic session network key
                [..]
            }
        """
        lenddev = self.service.add_lenddev(args[0], **kwargs)
        self.set_header("Location",
                        "/api/v1/lns/lenddevs/%s" % lenddev.dev_eui)

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all LoRaWAN end devices.

        Args:
            [0]: devEUI

        Example URLs:
            DELETE /api/v1/lns/lenddevs
            DELETE /api/v1/lns/lenddevs/00:28:A1:54:B8:91:72:D2
        """
        if args:
            self.service.remove_lenddev(EUI64(args[0]))
        else:
            self.service.remove_all_lenddevs()
