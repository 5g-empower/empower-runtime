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

"""LVNFP Protocol Server."""

import uuid
import tornado.web
import tornado.httpserver

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.core.image import Image
from empower.core.lvnf import LVNF

from empower.main import RUNTIME


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

            lvnf = LVNF(lvnf_id=lvnf_id,
                        tenant_id=tenant_id,
                        image=image,
                        cpp=cpp)

            lvnf.start()

            # the LVNF is added to the list because in this way its state is
            # maintained as spawning, then as a result of the lvnf status
            # message this can change to running or stopped.
            tenant.lvnfs[lvnf_id] = lvnf

        except ValueError as ex:
            self.send_error(400, message=ex)
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
