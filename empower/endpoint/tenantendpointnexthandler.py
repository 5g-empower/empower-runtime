#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""Tenant/Endpoint/Port/Next Handler."""

from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.main import RUNTIME

import uuid
import tornado.web


class TenantEndpointNextHandler(EmpowerAPIHandlerAdminUsers):
    """Tenant/Endpoint/Port/Next Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps" +
                r"/([a-zA-Z0-9-]*)/ports/([0-9]*)/next/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps" +
                r"/([a-zA-Z0-9-]*)/ports/([0-9]*)/next/([a-zA-Z0-9_:,=]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """List next associations.

        Args:
            [0]: the tenant id
            [1]: the endpoint id
            [2]: the port id
            [3]: match

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next/
                in_port=1,dl_type=800,nw_proto=84
        """

        try:

            if len(args) not in [3, 4]:
                raise ValueError("Invalid url")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = uuid.UUID(args[1])
            endpoint = tenant.endpoints[endpoint_id]

            port_id = int(args[2])
            port = endpoint.ports[port_id]

            if len(args) == 3:
                self.write_as_json(port.next)
            else:
                match = args[3]
                self.write_as_json(port.next[match])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(200, None)

    def post(self, *args, **kwargs):
        """Set next flow rules.

        Args:
            [0]: the tenant id
            [1]: the endpoint id
            [2]: the port id

        Example URLs:

            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next
        """

        try:

            if len(args) != 3:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "match" not in request:
                raise ValueError("missing match element")

            if "next" not in request:
                raise ValueError("missing next element")

            match = request['match']

            if not isinstance(match, str):
                raise ValueError("Field match must be a string")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = uuid.UUID(args[1])
            endpoint = tenant.endpoints[endpoint_id]

            port_id = int(args[2])
            port = endpoint.ports[port_id]

            next_type = request['next']['type'].lower()
            next_id = uuid.UUID(request['next']['uuid'])

            valid_types = ["lvnf", "ep"]

            if next_type not in valid_types:
                raise ValueError("invalid type, allowed are %s" % valid_types)

            next_obj = None
            if next_type == "lvnf":
                next_obj = tenant.lvnfs[next_id]
            elif next_type == "ep":
                next_obj = tenant.endpoints[next_id]

            if next_id == endpoint_id:
                raise ValueError("Loop detected")

            next_port_id = int(request['next']['port_id'])
            next_port = next_obj.ports[next_port_id]

            port.next[match] = next_port

            url = "/api/v1/tenants/%s/eps/%s/ports/%u/next/%s"
            tokens = (tenant_id, endpoint_id, port_id, match)

            self.set_header("Location", url % tokens)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """Delete next flow rules.

        Args:
            [0]: the tenant id
            [1]: the endpoint id
            [2]: the port id
            [3]: match

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                   eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next/
                   dl_src=00:18:DE:CC:D3:40;dpid=00:0D:B9:2F:56:64;port_id=2
        """

        try:

            if len(args) not in [3, 4]:
                raise ValueError("Invalid url")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = uuid.UUID(args[1])
            endpoint = tenant.endpoints[endpoint_id]

            port_id = int(args[2])
            port = endpoint.ports[port_id]

            if len(args) == 4:
                match = args[3]
            else:
                match = ""

            del port.next[match]

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)
