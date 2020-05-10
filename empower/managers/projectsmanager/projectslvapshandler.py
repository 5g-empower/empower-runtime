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

"""Exposes a RESTful interface ."""

import uuid

import empower_core.apimanager.apimanager as apimanager

from empower_core.etheraddress import EtherAddress
from empower.managers.ranmanager.lvapp.resourcepool import ResourcePool


# pylint: disable=W0223
class ProjectsLVAPsHandler(apimanager.APIHandler):
    """Handler for accessing LVAPs. in a project"""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/lvaps/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/lvaps/([a-zA-Z0-9:]*)/?"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """List the LVAPs.

        Args:

            [0], the project id (mandatory)
            [1]: the lvap address (optional)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvaps

            [
                {
                    "addr": "60:F4:45:D0:3B:FC",
                    "assoc_id": 732,
                    "association_state": true,
                    "authentication_state": true,
                    "blocks": [
                        ...
                    ],
                    "bssid": "52:31:3E:D0:3B:FC",
                    "encap": "00:00:00:00:00:00",
                    "ht_caps": true,
                    "ht_caps_info": {
                        "DSSS_CCK_Mode_in_40_MHz": false,
                        "Forty_MHz_Intolerant": false,
                        "HT_Delayed_Block_Ack": false,
                        "HT_Greenfield": false,
                        "LDPC_Coding_Capability": true,
                        "L_SIG_TXOP_Protection_Support": false,
                        "Maximum_AMSDU_Length": false,
                        "Reserved": false,
                        "Rx_STBC": 0,
                        "SM_Power_Save": 3,
                        "Short_GI_for_20_MHz": true,
                        "Short_GI_for_40_MHz": true,
                        "Supported_Channel_Width_Set": true,
                        "Tx_STBC": false
                    },
                    "networks": [
                        [
                            "52:31:3E:D0:3B:FC",
                            "EmPOWER"
                        ]
                    ],
                    "pending": [],
                    "ssid": "EmPOWER",
                    "state": "running",
                    "wtp": {
                        ...
                    }
                }
            ]

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvaps/
                60:F4:45:D0:3B:FC

            {
                "addr": "60:F4:45:D0:3B:FC",
                "assoc_id": 732,
                "association_state": true,
                "authentication_state": true,
                "blocks": [
                    ...
                ],
                "bssid": "52:31:3E:D0:3B:FC",
                "encap": "00:00:00:00:00:00",
                "ht_caps": true,
                "ht_caps_info": {
                    "DSSS_CCK_Mode_in_40_MHz": false,
                    "Forty_MHz_Intolerant": false,
                    "HT_Delayed_Block_Ack": false,
                    "HT_Greenfield": false,
                    "LDPC_Coding_Capability": true,
                    "L_SIG_TXOP_Protection_Support": false,
                    "Maximum_AMSDU_Length": false,
                    "Reserved": false,
                    "Rx_STBC": 0,
                    "SM_Power_Save": 3,
                    "Short_GI_for_20_MHz": true,
                    "Short_GI_for_40_MHz": true,
                    "Supported_Channel_Width_Set": true,
                    "Tx_STBC": false
                },
                "networks": [
                    [
                        "52:31:3E:D0:3B:FC",
                        "EmPOWER"
                    ]
                ],
                "pending": [],
                "ssid": "EmPOWER",
                "state": "running",
                "wtp": {
                    ...
                }
            }

        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        return project.lvaps \
            if len(args) == 1 else project.lvaps[EtherAddress(args[1])]

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def put(self, *args, **kwargs):
        """Modify the LVAP

        Args:

            [0], the project id (mandatory)
            [1]: the lvap address (mandatory)

        Example URLs:

            PUT /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvaps/
                60:F4:45:D0:3B:FC

            {
                "version": "1.0",
                "wtp": "04:F0:21:09:F9:AA"
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        lvap = project.lvaps[EtherAddress(args[1])]

        if "blocks" in kwargs:

            wtp = project.wtps[EtherAddress(kwargs['wtp'])]

            pool = ResourcePool()

            for block_id in kwargs["blocks"]:
                pool.append(wtp.blocks[block_id])

            lvap.blocks = pool

        elif "wtp" in kwargs:

            lvap.wtp = project.wtps[EtherAddress(kwargs['wtp'])]

        if "encap" in kwargs:

            encap = EtherAddress(kwargs["encap"])
            lvap.encap = encap
