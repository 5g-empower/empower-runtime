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

"""LVNF Port Handler."""

import uuid

from empower.restserver.apihandlers import EmpowerAPIHandlerUsers

from empower.main import RUNTIME


class TenantLVNFPortHandler(EmpowerAPIHandlerUsers):
    """Tenant/LVNF/Port Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvnfs" +
                "/([a-zA-Z0-9-]*)/ports/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvnfs" +
                "/([a-zA-Z0-9-]*)/ports/([0-9]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """ List all ports.

        Args:
            [0]: the tenant id
            [1]: the lvap id
            [2]: the port id

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvnfs/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvnfs/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1
        """

        try:

            if len(args) > 3 or len(args) < 2:
                raise ValueError("Invalid url")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            lvnf_id = uuid.UUID(args[1])
            lvnf = tenant.lvnfs[lvnf_id]

            if len(args) == 2:
                self.write_as_json(lvnf.ports.values())
                self.set_status(200, None)
            else:
                port_id = int(args[2])
                port = lvnf.ports[port_id]
                self.write_as_json(port)
                self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)
