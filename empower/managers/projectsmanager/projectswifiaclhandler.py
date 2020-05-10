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


# pylint: disable=W0223
class ProjectsWiFiACLHandler(apimanager.APIHandler):
    """Wi-Fi ACL handler"""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/wifi_acl/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/wifi_acl/([a-zA-Z0-9:]*)/?"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """Lists all clients in the ACL.

        Args:

            [0], the project id (mandatory)
            [0]: the device address (optional)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_acl/

            {
                "60:57:18:B1:A4:B8": {
                    "addr": "60:57:18:B1:A4:B8",
                    "desc": "Dell Laptop"
                },
                "18:5E:0F:E3:B8:68": {
                    "addr": "18:5E:0F:E3:B8:68",
                    "desc": "Dell Laptop"
                },
                "60:F4:45:D0:3B:FC": {
                    "addr": "60:F4:45:D0:3B:FC",
                    "desc": "Roberto's iPhone"
                }
            }

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_acl/60:57:18:B1:A4:B8

            {
                "addr": "60:57:18:B1:A4:B8",
                "desc": "Dell Laptop"
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        allowed = project.wifi_props.allowed

        return allowed if not args else allowed[str(EtherAddress(args[1]))]

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def put(self, *args, **kwargs):
        """Update entry in ACL.

        Args:

            [0], the project id (mandatory)
            [1]: the device address (mandatory)

        Example URLs:

            PUT /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_acl/60:57:18:B1:A4:B8

            {
                "desc": "Dell Laptop"
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        desc = "Generic Station" if 'desc' not in kwargs else kwargs['desc']
        addr = EtherAddress(args[1])

        project.upsert_acl(addr, desc)

    @apimanager.validate(returncode=201, min_args=1, max_args=1)
    def post(self, *args, **kwargs):
        """Add entry in ACL.

        Args:

            [0], the project id (mandatory)

        Example URLs:

            POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_acl

            {
                "addr": "60:57:18:B1:A4:B8",
                "desc": "Dell Laptop"
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        desc = "Generic Station" if 'desc' not in kwargs else kwargs['desc']
        addr = EtherAddress(kwargs['addr'])

        acl = project.upsert_acl(addr, desc)

        url = "/api/v1/projects/%s/wifi_acl/%s" % (project_id, acl.addr)

        self.set_header("Location", url)

    @apimanager.validate(returncode=204, min_args=1, max_args=2)
    def delete(self, *args, **kwargs):
        """Delete an entry in ACL.

        Args:

            [0], the project id (mandatory)
            [0]: the device address (mandatory)

        Example URLs:

            DELETE /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                wifi_acl/60:57:18:B1:A4:B8
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        if len(args) == 2:
            project.remove_acl(EtherAddress(args[1]))
        else:
            project.remove_acl()
