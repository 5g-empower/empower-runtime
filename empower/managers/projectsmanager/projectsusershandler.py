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
class ProjectsUsersHandler(apimanager.APIHandler):
    """Handler for accessing LVAPs. in a project"""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/users/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/users/([0-9]*)/?"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """List the users.

        Args:

            [0]: the UE IMSI(optional)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/users

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/users/
                222930100001114

        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        return project.users \
            if len(args) == 1 else project.users[int(args[1])]
