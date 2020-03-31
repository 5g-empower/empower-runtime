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


# pylint: disable=W0223
class AppCallbacksHandler(apimanager.EmpowerAPIHandler):
    """Apps handler."""

    URLS = [
        r"/api/v1/projects/([a-zA-Z0-9-]*)/apps/([a-zA-Z0-9-]*)/callbacks/?",
        r"/api/v1/projects/([a-zA-Z0-9-]*)/apps/([a-zA-Z0-9-]*)/callbacks/"
        "([a-z]*)/?"
    ]

    @apimanager.validate(min_args=2, max_args=3)
    def get(self, *args, **kwargs):
        """List the callback.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (optional)
            [2]: the callback (optional)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                0f91e8ad-1c2a-4b06-97f9-e34097c4c1d0/callbacks
            {
                default: {
                    type: "url",
                    name: "default",
                    callback: "http://www.domain.io/resource"
                }
            }

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                0f91e8ad-1c2a-4b06-97f9-e34097c4c1d0/callbacks/default

            {
                type: "url",
                name: "default",
                callback: "http://www.domain.io/resource"
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        service_id = uuid.UUID(args[1])
        service = project.services[service_id]

        return service.callbacks \
            if len(args) == 2 else service.callbacks[args[2]]

    @apimanager.validate(returncode=201, min_args=2, max_args=2)
    def post(self, *args, **kwargs):
        """Add a callback.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)

        Request:

            version: protocol version (1.0)
            name: the name of the callback (mandatory)
            callback: the callback URL (mandatory)

        Example URLs:

            POST /api/v1/workers
            {
                "version": "1.0",
                "name": "default",
                "callback_type": "rest"
                "callback": "http://www.domain.io/resource"
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        service_id = uuid.UUID(args[1])
        service = project.services[service_id]
        service.add_callback(name=kwargs['name'],
                             callback_type=kwargs['callback_type'],
                             callback=kwargs['callback'])

        self.set_header("Location",
                        "/api/v1/projects/%s/apps/%s/callback/%s" %
                        (project_id, service_id, kwargs['name']))

    @apimanager.validate(returncode=204, min_args=3, max_args=3)
    def delete(self, *args, **kwargs):
        """Stop a worker.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)
            [2]: the callback (mandatory)

        Example URLs:

            DELETE /api/v1/workers/08e14f40-6ebf-47a0-8baa-11d7f44cc228/default
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        service_id = uuid.UUID(args[1])
        service = project.services[service_id]

        service.rem_callback(name=args[2])
