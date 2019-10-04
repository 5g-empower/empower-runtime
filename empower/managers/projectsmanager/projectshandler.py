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

import empower.managers.apimanager.apimanager as apimanager

from empower.core.etheraddress import EtherAddress
from empower.core.resourcepool import ResourcePool


# pylint: disable=W0223
class ProjectsHandler(apimanager.EmpowerAPIHandler):
    """Projects handler"""

    URLS = [r"/api/v1/projects/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/?"]

    @apimanager.validate(min_args=0, max_args=1)
    def get(self, *args, **kwargs):
        """Lists all the projects.

        Args:

            [0], the project id (optional)

        Example URLs:

            GET /api/v1/projects

            [
                {
                    "bootstrap": {
                        "7069c865-8849-4840-9d96-e028663a5dcf": {
                            "name": "empower.apps.wifimobilitymanager.
                                wifimobilitymanager",
                            "params": {
                                "every": 2000,
                                "project_id": "52313ecb-9d00-4b7d-b873-
                                    b55d3d9ada26",
                                "service_id": "7069c865-8849-4840-9d96-
                                    e028663a5dcf"
                            }
                        }
                    },
                    "desc": "5G-EmPOWER Wi-Fi Network",
                    "lte_props": null,
                    "lte_slices": {
                        "0": {
                            "devices": {},
                            "properties": {
                                "rbgs": 2,
                                "ue_scheduler": 0
                            },
                            "slice_id": 0
                        }
                    },
                    "owner": "foo",
                    "project_id": "52313ecb-9d00-4b7d-b873-b55d3d9ada26",
                    "wifi_props": {
                        "allowed": [
                            "60:57:18:B1:A4:B8",
                            "18:5E:0F:E3:B8:68",
                            "60:F4:45:D0:3B:FC"
                        ],
                        "bssid_type": "unique",
                        "ssid": "EmPOWER"
                    },
                    "wifi_slices": {
                        "0": {
                            "devices": {
                                "00:0D:B9:30:3E:18": {
                                    "amsdu_aggregation": false,
                                    "quantum": 10000,
                                    "sta_scheduler": 1
                                }
                            },
                            "properties": {
                                "amsdu_aggregation": false,
                                "quantum": 10000,
                                "sta_scheduler": 1
                            },
                            "slice_id": 0
                        },
                        "80": {
                            "devices": {
                                "00:0D:B9:30:3E:18": {
                                    "amsdu_aggregation": false,
                                    "quantum": 10000,
                                    "sta_scheduler": 1
                                }
                            },
                            "properties": {
                                "amsdu_aggregation": false,
                                "quantum": 10000,
                                "sta_scheduler": 1
                            },
                            "slice_id": 80
                        }
                    }
                }
            ]

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26

            {
                "bootstrap": {
                    "7069c865-8849-4840-9d96-e028663a5dcf": {
                        "name": "empower.apps.wifimobilitymanager.
                            wifimobilitymanager",
                        "params": {
                            "every": 2000,
                            "project_id": "52313ecb-9d00-4b7d-b873-
                                b55d3d9ada26",
                            "service_id": "7069c865-8849-4840-9d96-
                                e028663a5dcf"
                        }
                    }
                },
                "desc": "5G-EmPOWER Wi-Fi Network",
                "lte_props": null,
                "lte_slices": {
                    "0": {
                        "devices": {},
                        "properties": {
                            "rbgs": 2,
                            "ue_scheduler": 0
                        },
                        "slice_id": 0
                    }
                },
                "owner": "foo",
                "project_id": "52313ecb-9d00-4b7d-b873-b55d3d9ada26",
                "wifi_props": {
                    "allowed": [
                        "60:57:18:B1:A4:B8",
                        "18:5E:0F:E3:B8:68",
                        "60:F4:45:D0:3B:FC"
                    ],
                    "bssid_type": "unique",
                    "ssid": "EmPOWER"
                },
                "wifi_slices": {
                    "0": {
                        "devices": {
                            "00:0D:B9:30:3E:18": {
                                "amsdu_aggregation": false,
                                "quantum": 10000,
                                "sta_scheduler": 1
                            }
                        },
                        "properties": {
                            "amsdu_aggregation": false,
                            "quantum": 10000,
                            "sta_scheduler": 1
                        },
                        "slice_id": 0
                    },
                    "80": {
                        "devices": {
                            "00:0D:B9:30:3E:18": {
                                "amsdu_aggregation": false,
                                "quantum": 10000,
                                "sta_scheduler": 1
                            }
                        },
                        "properties": {
                            "amsdu_aggregation": false,
                            "quantum": 10000,
                            "sta_scheduler": 1
                        },
                        "slice_id": 80
                    }
                }
            }
        """

        return self.service.projects \
            if not args else self.service.projects[uuid.UUID(args[0])]

    @apimanager.validate(returncode=201, min_args=0, max_args=1)
    def post(self, *args, **kwargs):
        """Create a new project.

        Args:

            [0], the project id (optional)

        Request:

            version: protocol version (1.0)
            desc: a human-readable description of the project
            owner: the username of the requester
            wifi_props: the Wi-Fi properties
            lte_props: the LTE properties
        """

        project_id = uuid.UUID(args[0]) if args else uuid.uuid4()

        wifi_props = kwargs['wifi_props'] if 'wifi_props' in kwargs else None
        lte_props = kwargs['lte_props'] if 'lte_props' in kwargs else None

        wifi_slcs = kwargs['wifi_slices'] if 'wifi_slices' in kwargs else None
        lte_slcs = kwargs['lte_slices'] if 'lte_slices' in kwargs else None

        project = self.service.create(project_id=project_id,
                                      desc=kwargs['desc'],
                                      owner=kwargs['owner'],
                                      wifi_props=wifi_props,
                                      lte_props=lte_props)

        if wifi_slcs:
            for wifi_slice in wifi_slcs:
                project.upsert_wifi_slice(**wifi_slice)

        if lte_slcs:
            for lte_slice in lte_slcs:
                project.upsert_lte_slice(**lte_slice)

        self.set_header("Location", "/api/v1/projects/%s" % project.project_id)

    @apimanager.validate(returncode=204, min_args=1, max_args=1)
    def put(self, *args, **kwargs):
        """Update a project.

        Args:

            [0], the project id (mandatory)

        Request:

            version: protocol version (1.0)
            desc: a human-readable description of the project
            wifi_props: the Wi-Fi properties
            lte_props: the LTE properties
        """

        project_id = uuid.UUID(args[0])

        wifi_props = kwargs['wifi_props'] if 'wifi_props' in kwargs else None
        lte_props = kwargs['lte_props'] if 'lte_props' in kwargs else None

        self.service.update(project_id=project_id,
                            wifi_props=wifi_props,
                            lte_props=lte_props)

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all projects.

        Args:

            [0], the projects id

        Example URLs:

            DELETE /api/v1/projects
            DELETE /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26
        """

        if args:
            self.service.remove(uuid.UUID(args[0]))
        else:
            self.service.remove_all()


# pylint: disable=W0223
class ProjectsWiFiSlicesHandler(apimanager.EmpowerAPIHandler):
    """Wi-Fi slices handler"""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/wifi_slices/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/wifi_slices/([0-9]*)/?"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """Lists all slices in a project.

        Args:

            [0], the project id (mandatory)
            [1], the slice id (optional)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_slices

            [
                {
                    "devices": {
                        "00:0D:B9:30:3E:18": {
                            "amsdu_aggregation": false,
                            "quantum": 10000,
                            "sta_scheduler": 1
                        }
                    },
                    "properties": {
                        "amsdu_aggregation": false,
                        "quantum": 10000,
                        "sta_scheduler": 1
                    },
                    "slice_id": 0
                },
                {
                    "devices": {
                        "00:0D:B9:30:3E:18": {
                            "amsdu_aggregation": false,
                            "quantum": 10000,
                            "sta_scheduler": 1
                        }
                    },
                    "properties": {
                        "amsdu_aggregation": false,
                        "quantum": 10000,
                        "sta_scheduler": 1
                    },
                    "slice_id": 80
                }
            ]

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_slices/0

            {
                "devices": {
                    "00:0D:B9:30:3E:18": {
                        "amsdu_aggregation": false,
                        "quantum": 10000,
                        "sta_scheduler": 1
                    }
                },
                "properties": {
                    "amsdu_aggregation": false,
                    "quantum": 10000,
                    "sta_scheduler": 1
                },
                "slice_id": 0
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        return project.wifi_slices \
            if len(args) == 1 else project.wifi_slices[str(args[1])]

    @apimanager.validate(returncode=201, min_args=0, max_args=1)
    def post(self, *args, **kwargs):
        """Create a new slice.

        Args:

            [0], the project id (mandatory)

        Request:

            version: protocol version (1.0)
            slice_id: the slice id
            properties: the properties for this slice
            devices: the properties for the devices
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]
        slice_id = project.upsert_wifi_slice(**kwargs)
        project.save()
        project.refresh_from_db()

        self.set_header("Location", "/api/v1/projects/%s/wifi_slices/%s" %
                        (project_id, slice_id))

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def put(self, *args, **kwargs):
        """Update a slice.

        Args:

            [0], the project id (mandatory)
            [1], the slice id (mandatory)

        Request:

            version: protocol version (1.0)
            slice_id: the slice id
            properties: the properties for this slice
            devices: the properties for the devices
        """

        project_id = uuid.UUID(args[0])
        slice_id = str(args[1])
        kwargs['slice_id'] = slice_id
        project = self.service.projects[project_id]
        project.upsert_wifi_slice(**kwargs)

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def delete(self, *args, **kwargs):
        """Delete a slice.

        Args:

            [0], the project id
            [1], the slice id

        Example URLs:

            DELETE /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_slices/80
        """

        project_id = uuid.UUID(args[0])
        slice_id = str(args[1])
        project = self.service.projects[project_id]
        project.delete_wifi_slice(slice_id)


# pylint: disable=W0223
class ProjectsLTESlicesHandler(apimanager.EmpowerAPIHandler):
    """LTE Slices handler"""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/lte_slices/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/lte_slices/([0-9]*)/?"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """Lists all slices in a project.

        Args:

            [0], the project id (mandatory)
            [1], the slice id (optional)
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        return project.lte_slices \
            if len(args) == 1 else project.lte_slices[str(args[1])]

    @apimanager.validate(returncode=201, min_args=0, max_args=1)
    def post(self, *args, **kwargs):
        """Create a new slice.

        Args:

            [0], the project id (mandatory)

        Request:

            version: protocol version (1.0)
            slice_id: the slice id
            properties: the properties for this slice
            devices: the properties for the devices
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]
        slice_id = project.upsert_lte_slice(**kwargs)
        project.save()
        project.refresh_from_db()

        self.set_header("Location", "/api/v1/projects/%s/lte_slices/%s" %
                        (project_id, slice_id))

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def put(self, *args, **kwargs):
        """Update slice.

        Args:

            [0], the project id (mandatory)
            [1], the slice id (mandatory)

        Request:

            version: protocol version (1.0)
            slice_id: the slice id
            properties: the properties for this slice
            devices: the properties for the devices
        """

        project_id = uuid.UUID(args[0])
        slice_id = str(args[1])
        kwargs['slice_id'] = slice_id
        project = self.service.projects[project_id]
        project.upsert_lte_slice(**kwargs)

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def delete(self, *args, **kwargs):
        """Delete a slice.

        Args:

            [0], the project id (mandatory)
            [1], the slice id (mandatory)

        Example URLs:

            DELETE /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lte_slices/80
        """

        project_id = uuid.UUID(args[0])
        slice_id = str(args[1])
        project = self.service.projects[project_id]
        project.delete_lte_slice(slice_id)


# pylint: disable=W0223
class ProjectLVAPsHandler(apimanager.EmpowerAPIHandler):
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

        lvap = project.lvaps[EtherAddress(args[0])]

        if "blocks" in kwargs:

            addr = EtherAddress(kwargs['wtp'])
            wtp = self.service.devices[addr]
            pool = ResourcePool()

            for block_id in kwargs["blocks"]:
                pool.append(wtp.blocks[block_id])

            lvap.blocks = pool

        elif "wtp" in kwargs:

            wtp = self.service.devices[EtherAddress(kwargs['wtp'])]
            lvap.wtp = wtp

        if "encap" in kwargs:

            encap = EtherAddress(kwargs["encap"])
            lvap.encap = encap
