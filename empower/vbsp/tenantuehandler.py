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

"""Tenant/UE Handler."""

import tornado.web
import tornado.httpserver
import uuid

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers

from empower.main import RUNTIME


class TenantUEHandler(EmpowerAPIHandlerUsers):
    """TenantUE handler. Used to view and manipulate UEs in tenants."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/ues/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/ues/([a-zA-Z0-9:]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all USe in a Pool or just the specified one.

        Args:
            pool_id: the network name
            imsi: the ue address

        Example URLs:
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/ues
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/ues/12345
        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid URL")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]
            ues = tenant.ues

            if len(args) == 1:
                self.write_as_json(ues.values())
            else:
                ue = int(args[1])
                self.write_as_json(ues[ue])

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(200, None)

    def put(self, *args, **kwargs):
        """ Set the cell for a given UE.

        Args:
            tenant_id: the tenant id
            imsi: the ue IMSI

        Request:
            version: the protocol version (1.0)

        Example URLs:
            PUT /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/ues/111
        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid URL")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "vbs" not in request:
                raise ValueError("missing vbs element")

            if "pci" not in request:
                raise ValueError("missing pci element")

            tenant_id = uuid.UUID(args[0])
            imsi = int(args[1])

            tenant = RUNTIME.tenants[tenant_id]
            ue = tenant.ues[imsi]

            vbs_addr = EtherAddress(request['vbs'])
            pci = int(request['pci'])

            vbs = tenant.vbses[vbs_addr]

            target = None
            for cell in vbs.cells:
                if cell.pci == pci:
                    target = cell

            if not target:
                raise KeyError("Cell %s/%u not found", vbs_addr, pci)

            ue.cell = target

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(204, None)
