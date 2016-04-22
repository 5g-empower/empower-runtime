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
