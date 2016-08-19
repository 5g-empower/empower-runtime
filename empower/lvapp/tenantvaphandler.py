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

"""VAPs Handerler."""

import uuid

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class TenantVAPHandler(EmpowerAPIHandlerUsers):
    """TenantVAP handler. Used to view and manipulate VAPs in tenants."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/vaps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/vaps/([a-zA-Z0-9:]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all VAPs in a Pool or just the specified one.

        Args:
            pool_id: the network name
            vap_id: the vap address

        Example URLs:
            GET /api/v1/pools/EmPOWER/vaps
            GET /api/v1/pools/EmPOWER/vaps/11:22:33:44:55:66
        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid URL")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]
            vaps = tenant.vaps

            if len(args) == 1:
                self.write_as_json(vaps.values())
            else:
                vap = EtherAddress(args[1])
                self.write_as_json(vaps[vap])

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(200, None)
