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
class ProjectsLTESlicesHandler(apimanager.APIHandler):
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
