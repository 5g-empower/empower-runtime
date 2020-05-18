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


# pylint: disable=W0223
class ProjectsHandler(apimanager.APIHandler):
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
                    },
                    "desc": "5G-EmPOWER Wi-Fi Network",
                    "lora_props": null,
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
                        "allowed": {
                            "04:46:65:49:e0:1f": {
                                "addr": "04:46:65:49:e0:1f",
                                "desc": "Some laptop"
                            },
                            "04:46:65:49:e0:11": {
                                "addr": "04:46:65:49:e0:1f",
                                "desc": "Some other laptop"
                            },
                            "04:46:65:49:e0:12": {
                                "addr": "04:46:65:49:e0:1f",
                                "desc": "Yet another laptop"
                            }
                        },
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
                },
                "desc": "5G-EmPOWER Wi-Fi Network",
                "lora_props": null,
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
                    "allowed": {
                        "04:46:65:49:e0:1f": {
                            "addr": "04:46:65:49:e0:1f",
                            "desc": "Some laptop"
                        },
                        "04:46:65:49:e0:11": {
                            "addr": "04:46:65:49:e0:1f",
                            "desc": "Some other laptop"
                        },
                        "04:46:65:49:e0:12": {
                            "addr": "04:46:65:49:e0:1f",
                            "desc": "Yet another laptop"
                        }
                    },
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
        lora_props = kwargs['lora_props'] if 'lora_props' in kwargs else None

        wifi_slcs = kwargs['wifi_slices'] if 'wifi_slices' in kwargs else None
        lte_slcs = kwargs['lte_slices'] if 'lte_slices' in kwargs else None

        project = self.service.create(project_id=project_id,
                                      desc=kwargs['desc'],
                                      owner=kwargs['owner'],
                                      wifi_props=wifi_props,
                                      lte_props=lte_props,
                                      lora_props=lora_props)

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
        """

        project_id = uuid.UUID(args[0])

        self.service.update(project_id=project_id, desc=kwargs['desc'])

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
