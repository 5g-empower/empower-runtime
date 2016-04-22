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
# WARRANTIES OF MERCHANTABILITfY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""PNF Protocol Server."""

import tornado.web
import tornado.ioloop
import tornado.websocket

from uuid import UUID

from empower.persistence import Session
from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandler
from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.persistence.persistence import TblBelongs

from empower.main import RUNTIME


class BasePNFDevHandler(EmpowerAPIHandler):
    """PNFDev handler. Used to view and manipulate PNFDevs."""

    HANDLERS = [(r"/api/v1/pnfdevs/?"),
                (r"/api/v1/pnfdevs/([a-zA-Z0-9:]*)/?")]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """ List all PNFDevs or a single PNFDev if the pnfdev_addr is
        specified. Returns 404 if pnfdev not exists.

        Args:
            pnfdev_addr: the address of the pnfdev

        Example URLs:

            GET /api/v1/pnfdev
            GET /api/v1/pnfdev/11:22:33:44:55:66

        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid url")

            if len(args) == 0:
                self.write_as_json(self.server.pnfdevs.values())
            else:
                pnfdev = self.server.pnfdevs[EtherAddress(args[0])]
                self.write_as_json(pnfdev)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args):
        """ Add a new PNFDev.

        Args:
            None

        Request:
            version: protocol version (1.0)
            pnfdev: the pnfdev address
            label: a description for this pnfdev

        Example URLs:

            POST /api/v1/pnfdev
        """

        try:

            if len(args) > 0:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "addr" not in request:
                raise ValueError("missing pnfdev element")

            if "label" not in request:
                label = "Generic PNFDev"
            else:
                label = request['label']

            addr = EtherAddress(request['addr'])
            self.server.add_pnfdev(addr, label)

            self.set_header("Location",
                            "/api/v1/pnfdevs/%s" % request['addr'])

        except ValueError as ex:
            self.send_error(400, message=ex)

        except RuntimeError as ex:
            self.send_error(400, message=ex)

        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """ Delete a PNFDev.

        Args:
            pnfdev_addr: the pnfdev address

        Example URLs:

            DELETE /api/v1/pnfdev/11:22:33:44:55:66
        """

        try:
            if len(args) != 1:
                raise ValueError("Invalid url")
            self.server.remove_pnfdev(EtherAddress(args[0]))
        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)
        self.set_status(204, None)


class BaseTenantPNFDevHandler(EmpowerAPIHandlerAdminUsers):
    """TenantPNFDevHandler Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/pnfdevs/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/pnfdevs/([a-zA-Z0-9:]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """ List all PNFDevs in a certain Tenant or a single ONFDev if the addr
        is specified. Returns 404 if either the tenant or the PNFDev do not
        exists.

        Args:
            tenant_id: the network names of the tenant
            addr: the address of the pnfdev

        Example URLs:

            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/pnfdev
            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                pnfdev/11:22:33:44:55:66

        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]
            tenant_pnfdevs = getattr(tenant, self.server.PNFDEV.ALIAS)

            if len(args) == 1:
                self.write_as_json(tenant_pnfdevs.values())
                self.set_status(200, None)
            else:
                addr = EtherAddress(args[1])
                pnfdev = tenant_pnfdevs[addr]
                self.write_as_json(pnfdev)
                self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args, **kwargs):
        """ Add a pnfdev to a tenant.

        Args:
            tenant_id: network name of a tenant
            addr: the address of a pnfdev

        Example URLs:

            POST /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                 pnfdev/11:22:33:44:55:66

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            addr = EtherAddress(args[1])

            tenant = RUNTIME.tenants[tenant_id]
            pnfdev = self.server.pnfdevs[addr]

            tenant.add_pnfdev(pnfdev)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def delete(self, *args, **kwargs):
        """ Remove a pnfdev from a Tenant.

        Args:
            tenant_id: network name of a tenant
            addr: the address of a pnfdev

        Example URLs:

            DELETE /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                   pnfdev/11:22:33:44:55:66

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            addr = EtherAddress(args[1])

            tenant = RUNTIME.tenants[tenant_id]
            tenant_pnfdevs = getattr(tenant, self.server.PNFDEV.ALIAS)
            pnfdev = tenant_pnfdevs[addr]

            tenant.remove_pnfdev(pnfdev)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)
        self.set_status(204, None)


class PNFPServer():
    """Exposes the PNF Protocol API."""

    PNFDEV = None
    TBL_PNFDEV = None

    def __init__(self, pt_types, pt_types_handlers):

        self.port = None
        self.__load_pnfdevs()
        self.__load_belongs()
        self.pt_types = pt_types
        self.pt_types_handlers = pt_types_handlers

    @property
    def pnfdevs(self):
        """Return PNFDevs."""

        return getattr(RUNTIME, self.PNFDEV.ALIAS)

    def __load_pnfdevs(self):
        """Load PNFDevs."""

        pnfdevs = Session().query(self.TBL_PNFDEV).all()

        for pnfdev in pnfdevs:

            if pnfdev.addr in self.pnfdevs:
                raise KeyError(pnfdev.addr)

            self.pnfdevs[pnfdev.addr] = \
                self.PNFDEV(pnfdev.addr, pnfdev.label)

    def __load_belongs(self):
        """Load Tenant/PNFDevs relationship."""

        for belongs in Session().query(TblBelongs).all():

            if belongs.addr not in self.pnfdevs:
                continue

            if belongs.tenant_id not in RUNTIME.tenants:
                raise KeyError("Tenant not found %s", belongs.tenant_id)

            pnfdev = self.pnfdevs[belongs.addr]
            tenant = RUNTIME.tenants[belongs.tenant_id]
            tenant_pnfdevs = getattr(tenant, self.PNFDEV.ALIAS)

            tenant_pnfdevs[pnfdev.addr] = pnfdev

    def to_dict(self):
        """ Return a dict representation of the object. """

        return {'port': self.port}

    def add_pnfdev(self, addr, label):
        """Add PNFDev."""

        if addr in self.pnfdevs:
            raise KeyError(addr)

        self.pnfdevs[addr] = self.PNFDEV(addr, label)

        session = Session()
        session.add(self.TBL_PNFDEV(addr=addr, label=label))
        session.commit()

        return self.pnfdevs[addr]

    def remove_pnfdev(self, addr):
        """Remove PNFDev."""

        if addr not in self.pnfdevs:
            raise KeyError(addr)

        pnfdev = self.pnfdevs[addr]

        for tenant in RUNTIME.tenants.values():

            tenant_pnfdevs = getattr(tenant, self.PNFDEV.ALIAS)

            if addr in tenant_pnfdevs:
                tenant.remove_pnfdev(pnfdev)

        del self.pnfdevs[addr]

        pnfdev = Session().query(self.TBL_PNFDEV) \
            .filter(self.TBL_PNFDEV.addr == addr) \
            .first()

        session = Session()
        session.delete(pnfdev)
        session.commit()

    def register_message(self, pt_type, parser, handler):
        """ Register new handler. This will be called after the default. """

        if pt_type not in self.pt_types:
            self.pt_types[pt_type] = parser

        if pt_type not in self.pt_types_handlers:
            self.pt_types_handlers[pt_type] = []

        if handler:
            self.pt_types_handlers[pt_type].append(handler)
