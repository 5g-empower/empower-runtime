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
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbses/([a-zA-Z0-9:]*)/ues/",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/vbses/([a-zA-Z0-9:]*)/ues/([a-zA-Z0-9]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all UEs of a tenant or just the specified one.
            An UE can be uniquely identified using the VBS ID and RNTI.
        Args:
            tenant_id: the network identifier
            vbs_id: the vbs identifier
            rnti: the radio network temporary identifier
        Example URLs:
            GET /api/v1/tenants/478644a7-f5c8-4a6e-9102-5b56c86e89f1/ues
            GET /api/v1/tenants/478644a7-f5c8-4a6e-9102-5b56c86e89f1/vbses/11:22:33:44:55:66/ues/f93b
        """

        try:

            if len(args) > 3 or len(args) < 1:
                raise ValueError("Invalid URL")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]
            ues = tenant.ues

            if len(args) == 1:
                self.write_as_json(ues.values())
            else:
                vbs_id = EtherAddress(args[1])

                if vbs_id not in RUNTIME.vbses:
                    raise ValueError("Invalid VBS ID")

                vbs_ues = []

                for ue in ues.values():
                    if ue.vbs.addr == vbs_id:
                        vbs_ues.append(ue)

                if len(args) == 2:
                    self.write_as_json(vbs_ues)
                else:
                    if len(vbs_ues) == 0:
                        raise ValueError("Invalid UE RNTI")

                    rnti = int(args[2])

                    for ue in vbs_ues:
                        if ue.rnti == rnti:
                            self.write_as_json(ue)
                            break

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(200, None)
