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

"""LVNFP Protocol Server."""

import uuid
import tornado.web
import tornado.httpserver

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.core.image import Image
from empower.core.lvnf import LVNF

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class TenantLVNFHandler(EmpowerAPIHandlerAdminUsers):
    """Tenant Function Handler. Used to view anc manipulate Functions."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvnfs/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvnfs/([a-zA-Z0-9-]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """ List all Functions.

        Args:
            tenant_id: the network names of the tenant
            lvnf_id: the address of the cpp

        Example URLs:

            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvnfs
            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvnfs/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid url")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            if len(args) == 1:
                self.write_as_json(tenant.lvnfs.values())
                self.set_status(200, None)
            else:
                lvnf_id = uuid.UUID(args[1])
                lvnf = tenant.lvnfs[lvnf_id]
                self.write_as_json(lvnf)
                self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args, **kwargs):
        """ Add an LVNF to a tenant.

        Args:
            tenant_id: network name of a tenant
            lvnf_id: the lvnf id

        Example URLs:

            POST /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvnfs
            POST /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvnfs/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "image" not in request:
                raise ValueError("missing image element")

            if "addr" not in request:
                raise ValueError("missing addr element")

            if "nb_ports" not in request['image']:
                raise ValueError("missing image/nb_ports element")

            if "vnf" not in request['image']:
                raise ValueError("missing image/vnf element")

            handlers = []

            if "handlers" in request['image']:
                handlers = request['image']['handlers']

            state_handlers = []

            if "state_handlers" in request['image']:
                state_handlers = request['image']['state_handlers']

            tenant_id = uuid.UUID(args[0])
            addr = EtherAddress(request['addr'])

            tenant = RUNTIME.tenants[tenant_id]
            cpp = tenant.cpps[addr]

            image = Image(nb_ports=request['image']['nb_ports'],
                          vnf=request['image']['vnf'],
                          state_handlers=state_handlers,
                          handlers=handlers)

            if not cpp.connection:
                raise ValueError("CPP disconnected %s" % addr)

            if len(args) == 1:
                lvnf_id = uuid.uuid4()
            else:
                lvnf_id = uuid.UUID(args[1])

            if lvnf_id in tenant.lvnfs:
                raise ValueError("already defined %s" % lvnf_id)

            lvnf = LVNF(lvnf_id=lvnf_id,
                        tenant_id=tenant_id,
                        image=image,
                        cpp=cpp)

            lvnf.start()

        #except ValueError as ex:
        #    self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def put(self, *args, **kwargs):
        """ Add an LVNF to a tenant.

        Args:
            [0]: the tenant id
            [1]: the lvnf id

        Example URLs:

            PUT /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvnfs/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "addr" not in request:
                raise ValueError("missing addr element")

            tenant_id = uuid.UUID(args[0])
            lvnf_id = uuid.UUID(args[1])

            addr = EtherAddress(request['addr'])

            tenant = RUNTIME.tenants[tenant_id]
            cpp = tenant.cpps[addr]
            lvnf = tenant.lvnfs[lvnf_id]

            if not cpp.connection:
                raise ValueError("CPP disconnected %s" % addr)

            lvnf.cpp = cpp

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def delete(self, *args, **kwargs):
        """ Remove an lvnf from a Tenant.

        Args:
            tenant_id: network name of a tenant
            lvnf_id: the lvnf_id

        Example URLs:

            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                lvnfs/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            lvnf_id = uuid.UUID(args[1])
            lvnf = tenant.lvnfs[lvnf_id]

            lvnf.stop()

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)
