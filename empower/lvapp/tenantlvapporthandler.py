#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""LVAP Port Handler."""

import uuid

from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.datatypes.etheraddress import EtherAddress

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class TenantLVAPPortHandler(EmpowerAPIHandlerAdminUsers):
    """Tenant/LVAP/Port Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvaps" +
                "/([a-zA-Z0-9:]*)/ports/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvaps" +
                "/([a-zA-Z0-9:]*)/ports/([0-9]*)/?"]

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
                lvaps/00:14:d3:45:aa:5c/ports

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvaps/00:14:d3:45:aa:5c/ports/1
        """

        try:

            if len(args) > 3 or len(args) < 2:
                raise ValueError("Invalid url")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            lvap_id = EtherAddress(args[1])
            lvap = tenant.lvaps[lvap_id]

            if len(args) == 2:
                self.write_as_json(lvap.ports.values())
                self.set_status(200, None)
            else:
                port_id = int(args[2])
                port = lvap.ports[port_id]
                self.write_as_json(port)
                self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)
