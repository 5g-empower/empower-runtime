#!/usr/bin/env python3
#
# Copyright (c) 2021 Roberto Riggio
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

"""Beacon Handlers."""

import empower_core.apimanager.apimanager as apimanager

from empower_core.etheraddress import EtherAddress
from empower_core.ssid import SSID


# pylint: disable=W0223
class BeaconHandler(apimanager.APIHandler):
    """Handler for accessing WTPs."""

    URLS = [r"/api/v1/wtps/([a-zA-Z0-9:]*)/blocks/([0-9]*)/beacon?"]

    @apimanager.validate(returncode=201, min_args=2, max_args=2)
    def post(self, *args, **kwargs):
        """Add a new device.

        Request:

            version: protocol version (1.0)
            dst: the beacon destination address
            bssid: the beacon BSSID address
            ssid: the SSID

        Example URLs:

            POST /api/v1/wtps/00:0D:B9:2F:56:64/blocks/1/beacon

            {
                "version":"1.0",
                "dst": "FF:FF:FF:FF:FF:FF",
                "bssid": "00:0D:B9:2F:56:64",
                "desc": "Test beacon"
            }
        """

        wtp = self.service.devices[EtherAddress(args[0])]
        block = wtp.blocks[int(args[1])]

        dst = EtherAddress(kwargs['dst'])
        bssid = EtherAddress(kwargs['bssid'])
        ssid = SSID(kwargs['ssid'])

        wtp.connection.send_trigger_beacon(block.block_id, dst, bssid, ssid)
