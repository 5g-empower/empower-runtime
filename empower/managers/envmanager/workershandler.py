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
class WorkerAttributesHandler(apimanager.EmpowerAPIHandler):
    """Access workers' attributes."""

    URLS = [r"/api/v1/workers/([a-zA-Z0-9-]*)/([a-zA-Z0-9_]*)/?"]

    @apimanager.validate(min_args=2, max_args=2)
    def get(self, *args, **kwargs):
        """Access a particular property of a worker.

        Args:

            [0]: the worker id (mandatory)
            [1]: the attribute of the worker to be accessed (mandatory)

        Example URLs:

            GET /api/v1/workers/0f91e8ad-1c2a-4b06-97f9-e34097c4c1d0/every

            [
                2000
            ]
        """

        service_id = uuid.UUID(args[0])
        service = self.service.env.services[service_id]

        if not hasattr(service, args[1]):
            raise KeyError("'%s' object has no attribute '%s'" %
                           (service.__class__.__name__, args[1]))

        return [getattr(service, args[1])]

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def put(self, *args, **kwargs):
        """Set a particular property of a worker.

        Args:

            [0]: the worker id (mandatory)
            [1]: the attribute of the worker to be accessed (mandatory)

        Example URLs:

            PUT /api/v1/workers/7069c865-8849-4840-9d96-e028663a5dcf/every
            {
                "version": "1.0",
                "value": 2000
            }
        """

        service_id = uuid.UUID(args[0])
        service = self.service.env.services[service_id]

        if not hasattr(service, args[1]):
            raise KeyError("'%s' object has no attribute '%s'" %
                           (service.__class__.__name__, args[1]))

        return setattr(service, args[1], kwargs["value"])


# pylint: disable=W0223
class WorkersHandler(apimanager.EmpowerAPIHandler):
    """Workers handler."""

    URLS = [r"/api/v1/workers/?",
            r"/api/v1/workers/([a-zA-Z0-9-]*)/?"]

    @apimanager.validate(min_args=0, max_args=1)
    def get(self, *args, **kwargs):
        """List the workers.

        Args:

            [0]: the worker id (optional)

        Example URLs:

            GET /api/v1/workers

            [
                {
                    "name":
                        "empower.workers.wifichannelstats.wifichannelstats",
                    "params": {
                        "every": 2000,
                        "project_id": "4cd2bca2-8c28-4e66-9c8a-7cbd1ba4e6f9",
                        "service_id": "0f91e8ad-1c2a-4b06-97f9-e34097c4c1d0"
                    }
                }
            ]

            GET /api/v1/workers/0f91e8ad-1c2a-4b06-97f9-e34097c4c1d0

            {
                "name": "empower.workers.wifichannelstats.wifichannelstats",
                "params": {
                    "every": 2000,
                    "project_id": "4cd2bca2-8c28-4e66-9c8a-7cbd1ba4e6f9",
                    "service_id": "0f91e8ad-1c2a-4b06-97f9-e34097c4c1d0"
                }
            }
        """

        return self.service.env.services \
            if not args else self.service.env.services[uuid.UUID(args[0])]

    @apimanager.validate(returncode=201, min_args=0, max_args=0)
    def post(self, *args, **kwargs):
        """Start a new worker.

        Request:

            version: protocol version (1.0)
            name: the name of the worker (mandatory)
            params: the list of parmeters to be set (optional)

        Example URLs:

            POST /api/v1/workers
            {
                "version": "1.0",
                "name": "empower.workers.wifichannelstats.wifichannelstats",
                "params": {
                    "every": 5000
                }
            }
        """

        service_id = uuid.UUID(args[0]) if args else uuid.uuid4()
        params = kwargs['params'] if 'params' in kwargs else {}

        service = \
            self.service.env.register_service(service_id=service_id,
                                              name=kwargs['name'],
                                              params=params)

        self.set_header("Location", "/api/v1/workers/%s" % service.service_id)

    @apimanager.validate(returncode=204, min_args=1, max_args=1)
    def put(self, *args, **kwargs):
        """Update the configuration of a worker.

        Args:

            [0], the worker id (mandatory)

        Request:

            version: protocol version (1.0)
            params: the list of parmeters to be set (optional)

        Example URLs:

            PUT /api/v1/workers/08e14f40-6ebf-47a0-8baa-11d7f44cc228
            {
                "version": "1.0",
                "params":
                {
                    "every": 5000
                }
            }
        """

        service_id = uuid.UUID(args[0])
        params = kwargs['params'] if 'params' in kwargs else {}

        self.service.env.reconfigure_service(service_id=service_id,
                                             params=params)

    @apimanager.validate(returncode=204, min_args=1, max_args=1)
    def delete(self, *args, **kwargs):
        """Stop a worker.

        Args:

            [0], the worker id

        Example URLs:

            DELETE /api/v1/workers/08e14f40-6ebf-47a0-8baa-11d7f44cc228
        """

        service_id = uuid.UUID(args[0])

        self.service.env.unregister_service(service_id=service_id)
