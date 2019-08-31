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
class AppAttributesHandler(apimanager.EmpowerAPIHandler):
    """Access applications' attributes."""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/apps/([a-zA-Z0-9-]*)/"
            "([a-zA-Z0-9_]*)/?"]

    @apimanager.validate(min_args=3, max_args=3)
    def get(self, *args, **kwargs):
        """Access a particular property of an application.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)
            [2]: the attribute of the app to be accessed (mandatory)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                7069c865-8849-4840-9d96-e028663a5dcf/stats

            [
                {
                    "last_run": "2019-08-23 09:46:52.361966"
                }
            ]
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        service_id = uuid.UUID(args[1])
        service = project.services[service_id]

        if not hasattr(service, args[2]):
            raise KeyError("'%s' object has no attribute '%s'" %
                           (service.__class__.__name__, args[2]))

        return [getattr(service, args[2])]

    @apimanager.validate(returncode=204, min_args=3, max_args=3)
    def put(self, *args, **kwargs):
        """Set a particular property of an application.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)
            [2]: the attribute of the app to be accessed (mandatory)

        Example URLs:

            PUT /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                7069c865-8849-4840-9d96-e028663a5dcf/stats

            {
                "version": "1.0",
                "value": {
                    "last_run": "2019-08-23 09:46:52.361966"
                }
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        service_id = uuid.UUID(args[1])
        service = project.services[service_id]

        if not hasattr(service, args[2]):
            raise KeyError("'%s' object has no attribute '%s'" %
                           (service.__class__.__name__, args[2]))

        return setattr(service, args[2], kwargs["value"])


# pylint: disable=W0223
class AppsHandler(apimanager.EmpowerAPIHandler):
    """Applications handler."""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/apps/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/apps/([a-zA-Z0-9-]*)/?"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """List the apps.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (optional)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps

            [
                {
                    "counters": {},
                    "name":
                        "empower.apps.wifimobilitymanager.wifimobilitymanager",
                    "params": {
                        "every": 2000,
                        "project_id": "52313ecb-9d00-4b7d-b873-b55d3d9ada26",
                        "service_id": "7069c865-8849-4840-9d96-e028663a5dcf"
                    },
                    "stats": {
                        "last_run": "2019-08-23 09:45:20.234651"
                    }
                }
            ]

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                7069c865-8849-4840-9d96-e028663a5dcf

            {
                "counters": {},
                "name": "empower.apps.wifimobilitymanager.wifimobilitymanager",
                "params": {
                    "every": 2000,
                    "project_id": "52313ecb-9d00-4b7d-b873-b55d3d9ada26",
                    "service_id": "7069c865-8849-4840-9d96-e028663a5dcf"
                },
                "stats": {
                    "last_run": "2019-08-23 09:47:04.361268"
                }
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        return project.services \
            if len(args) == 1 else project.services[uuid.UUID(args[1])]

    @apimanager.validate(returncode=201, min_args=1, max_args=2)
    def post(self, *args, **kwargs):
        """Start a new app.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (optional)

        Request:

            version: protocol version (1.0)
            params: the list of parmeters to be set

        Example URLs:

            POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps

            {
                "version": "1.0",
                "name": "empower.apps.wifimobilitymanager.wifimobilitymanager",
                "params": {
                    "every": 5000
                }
            }

            POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                7069c865-8849-4840-9d96-e028663a5dcf

            {
                "version": "1.0",
                "name": "empower.apps.wifimobilitymanager.wifimobilitymanager",
                "params": {
                    "every": 5000
                }
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]

        service_id = uuid.UUID(args[1]) if len(args) > 1 else uuid.uuid4()
        params = kwargs['params'] if 'params' in kwargs else {}

        service = project.register_service(service_id=service_id,
                                           name=kwargs['name'],
                                           params=params)

        self.set_header("Location", "/api/v1/projects/%s/apps/%s" %
                        (project.project_id, service.service_id))

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def put(self, *args, **kwargs):
        """Update the configuration of an applications.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)

        Request:

            version: protocol version (1.0)
            params: the list of parmeters to be set

        Example URLs:

            PUT /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                7069c865-8849-4840-9d96-e028663a5dcf

            {
                "version": "1.0",
                "params": {
                    "every": 5000
                }
            }
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]
        service_id = uuid.UUID(args[1])
        params = kwargs['params'] if 'params' in kwargs else {}

        project.reconfigure_service(service_id, params)

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def delete(self, *args, **kwargs):
        """Stop an app.

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)

        Example URLs:

            DELETE /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                7069c865-8849-4840-9d96-e028663a5dcf
        """

        project_id = uuid.UUID(args[0])
        project = self.service.projects[project_id]
        service_id = uuid.UUID(args[1])

        project.unregister_service(service_id)
