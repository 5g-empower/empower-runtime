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

"""Endpoints Handler ."""

import tornado.web
import tornado.httpserver

from uuid import UUID, uuid4
from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.core.image import Image
from empower.core.lvnf import LVNF

from empower.main import RUNTIME


class TenantEndpointHandler(EmpowerAPIHandlerAdminUsers):
    """TenantCPPHandler Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps/([a-zA-Z0-9-]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """ List all Functions.

        Args:
            tenant_id: the network names of the tenant
            endpoint_id: the endpoint uuid

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/eps
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            if len(args) == 1:
                self.write_as_json(tenant.endpoints.values())
                self.set_status(200, None)
            else:
                endpoint_id = UUID(args[1])
                endpoint = tenant.endpoints[endpoint_id]
                self.write_as_json(endpoint)
                self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args):
        """Add a new Endpoint.

        Args:
            tenant_id: network name of a tenant
            endpoint_id: the endpoint id

        Request:
            version: protocol version (1.0)
            endpoint_name: the endpoint name
            desc: a description for this endpoint
            ports: a dictionary of VirtualPorts, where each key is a vport_id
                dpid: the datapath id of the vport
                port_id: the vport port number on the datapath id
                iface: the interface name
                hwaddr: the mac address of the interface
                        (or any other custom address)
                learn_host: if True, the hwaddr is bounded to that interface

        Example URLs:

            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/eps
            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34
        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "endpoint_name" not in request:
                raise ValueError("missing endpoint_name element")

            if "desc" not in request:
                desc = "Generic description"
            else:
                desc = request['desc']

            if "ports" not in request:
                raise ValueError("missing ports element")

            if type(request["ports"]) is not dict:
                raise ValueError("ports is not a dictionary")

            for port in request["ports"].values():

                if "dpid" not in port:
                    raise ValueError("missing dpid element")

                if "port_id" not in port:
                    raise ValueError("missing port_id element")

                if "iface" not in port:
                    raise ValueError("missing iface element")

                if "hwaddr" not in port:
                    raise ValueError("missing hwaddr element")

                if "learn_host" not in port:
                    raise ValueError("missing learn_host element")

            tenant_id = UUID(args[0])

            if len(args) == 1:
                endpoint_id = uuid4()
            else:
                endpoint_id = UUID(args[1])

            self.server.add_endpoint(endpoint_id,
                                     tenant_id,
                                     request["endpoint_name"],
                                     desc,
                                     request["ports"])

            self.set_header("Location", "/api/v1/tenants/%s/eps/%s"
                            % (tenant_id, endpoint_id))

        except ValueError as ex:
            self.send_error(400, message=ex)

        except RuntimeError as ex:
            self.send_error(400, message=ex)

        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """ Remove an lvnf from a Tenant.

        Args:
            tenant_id: network name of a tenant
            endpoint_id: the endpoint_id

        Example URLs:

            Delete /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            endpoint_id = UUID(args[1])

            self.server.remove_endpoint(endpoint_id, tenant_id)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)
