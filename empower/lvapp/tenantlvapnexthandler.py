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

"""Tenant/LVAP/Port/Next Handler."""

import uuid
import tornado.web

from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.datatypes.etheraddress import EtherAddress
from empower.core.intent import match_to_key

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class TenantLVAPNextHandler(EmpowerAPIHandlerAdminUsers):
    """Tenant/LVAP/Port/Next Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvaps" +
                "/([a-zA-Z0-9:]*)/ports/([0-9]*)/next/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvaps" +
                "/([a-zA-Z0-9:]*)/ports/([0-9]*)/next/([a-zA-Z0-9_:;=]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """List next associations.

        Args:
            [0]: the tenant id
            [1]: the lvap id
            [2]: the port id

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvaps/00:14:d3:45:aa:5c/ports/1/next
        """

        try:

            if len(args) < 3 or len(args) > 4:
                raise ValueError("Invalid url")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            lvap_id = EtherAddress(args[1])
            lvap = tenant.lvaps[lvap_id]

            port_id = int(args[2])
            port = lvap.ports[port_id]

            output = {}

            for match, value in port.next.items():

                output[match] = value.to_dict() if value else {}
                output[match]['uuid'] = port.next.uuids[match]
                output[match]['match'] = match_to_key(match)
                output[match]['unparsed'] = match

            if len(args) == 4:
                self.write_as_json(output[args[3]])
            else:
                self.write_as_json(output.values())

            self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def put(self, *args, **kwargs):
        """Set next flow rules.

        Args:
            [0]: the tenant id
            [1]: the lvap id
            [2]: the port id

        Example URLs:

            PUT /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvaps/00:14:d3:45:aa:5c/ports/1/next
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

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            lvap_id = EtherAddress(args[1])
            lvap = tenant.lvaps[lvap_id]

            port_id = int(args[2])
            port = lvap.ports[port_id]

            next_lvnf_id = uuid.UUID(request['next']['lvnf_id'])
            next_lvnf = tenant.lvnfs[next_lvnf_id]

            next_port_id = int(request['next']['port_id'])
            next_port = next_lvnf.ports[next_port_id]

            match = request['match']
            port.next[match] = next_port

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def delete(self, *args, **kwargs):
        """Delete next flow rules.

        Args:
            [0]: the tenant id
            [1]: the lvap id
            [2]: the port id

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                   lvaps/00:14:d3:45:aa:5c/ports/1/next/
                   dl_src=00:18:DE:CC:D3:40;dpid=00:0D:B9:2F:56:64;port_id=2
        """

        print("ciao")

        try:

            if len(args) != 3:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "match" not in request:
                raise ValueError("missing match element")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            lvap_id = EtherAddress(args[1])
            lvap = tenant.lvaps[lvap_id]

            port_id = int(args[2])
            port = lvap.ports[port_id]

            match = request['match']

            del port.next[match]

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)
