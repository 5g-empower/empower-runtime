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
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class TenantUEHandler(EmpowerAPIHandlerUsers):
    """TenantUE handler. Used to view and manipulate UEs in tenants."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/ues/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/ues/([a-zA-Z0-9:]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all UEs in a Pool or just the specified one.

        Args:
            tenant_id: the network name
            ue_id: the ue address

        Example URLs:
            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/ues
            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/ues/11:22:33:44:55:66
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
                ue_addr = EtherAddress(args[1])
                self.write_as_json(ues[ue_addr])

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(200, None)
