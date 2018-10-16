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

"""PNF Protocol Server."""

import json

from uuid import UUID

import empower.logger

from empower.persistence import Session
from empower.core.slice import Slice
from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandler
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers
from empower.persistence.persistence import TblSlice
from empower.persistence.persistence import TblSliceBelongs
from empower.restserver.validate import validate

from empower.main import RUNTIME


class BasePNFDevHandler(EmpowerAPIHandler):
    """PNFDev handler. Used to view and manipulate PNFDevs."""

    HANDLERS = []

    def initialize(self, server):
        self.server = server

    @validate(max_args=1)
    def get(self, *args, **kwargs):
        """List PNFDevs.

        Args:

            [0]: the pnfdev address

        Example URLs:

            GET /api/v1/<wtps|cpps|vbses>
            GET /api/v1/<wtps|cpps|vbses>/11:22:33:44:55:66
        """

        return self.server.pnfdevs.values() \
            if not args else self.server.pnfdevs[EtherAddress(args[0])]

    @validate(returncode=201,
              input_schema={
                  "version" : {"type": float, "mandatory": True},
                  "addr" : {"type": EtherAddress, "mandatory": True},
                  "label" : {"type": str, "mandatory": False}
              })
    def post(self, *args, **kwargs):
        """Add a new PNFDev.

        Request:

            version: protocol version (1.0)
            addr: the pnfdev address
            label: a description for this pnfdev

        Example URLs:

            POST /api/v1/<wtps|cpps|vbses>
        """

        label = kwargs['label'] if 'label' in kwargs else "Generic Device"
        pnfdev = self.server.add_pnfdev(kwargs['addr'], label)
        url = "/api/v1/%s/%s" % (pnfdev.ALIAS, kwargs['addr'])
        self.set_header("Location", url)

    @validate(returncode=204, min_args=1, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete a PNFDev.

        Args:
            [0]]: the pnfdev address

        Example URLs:

            DELETE /api/v1/<wtps|cpps|vbses>/11:22:33:44:55:66
        """

        self.server.remove_pnfdev(EtherAddress(args[0]))


class BaseTenantPNFDevHandler(EmpowerAPIHandlerUsers):
    """TenantPNFDevHandler Handler."""

    HANDLERS = []

    def initialize(self, server):
        self.server = server

    @validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """List PNFDevs.

        Args:

            [0]: the tenant id
            [1]: the pnfdev address

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
              <wtps|cpps|vbses>
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
              <wtps|cpps|vbses>/11:22:33:44:55:66
        """

        tenant = RUNTIME.tenants[UUID(args[0])]
        pnfdevs = getattr(tenant, self.server.PNFDEV.ALIAS)

        return pnfdevs.values() \
            if len(args) != 2 else pnfdevs[EtherAddress(args[1])]


class PNFPServer:
    """Exposes the PNF Protocol API."""

    PNFDEV = None
    TBL_PNFDEV = None

    def __init__(self, port, pt_types, pt_types_handlers):

        self.port = port
        self.__load_pnfdevs()
        self.__load_slices()
        self.log = empower.logger.get_logger()
        self.pt_types = pt_types
        self.pt_types_handlers = pt_types_handlers

    def __load_slices(self):
        """Load Slices."""

        slices = Session().query(TblSlice).all()

        for slc in slices:

            tenant = RUNTIME.tenants[slc.tenant_id]

            desc = {'dscp': slc.dscp,
                    'wtps': {},
                    'vbses': {},
                    'wifi': json.loads(slc.wifi),
                    'lte': json.loads(slc.lte)}

            if slc.dscp not in tenant.slices:
                tenant.slices[slc.dscp] = Slice(slc.dscp, tenant, desc)

            t_slice = tenant.slices[slc.dscp]

            belongs = \
                Session().query(TblSliceBelongs) \
                         .filter(TblSliceBelongs.dscp == slc.dscp) \
                         .filter(TblSliceBelongs.tenant_id == slc.tenant_id) \
                         .all()

            for belong in belongs:

                if belong.addr not in self.pnfdevs:
                    continue

                pnfdev = self.pnfdevs[belong.addr]
                pnfdevs = None

                if pnfdev.ALIAS == "vbses":
                    pnfdevs = t_slice.lte[pnfdev.ALIAS]

                    if pnfdev.addr not in pnfdevs:
                        pnfdevs[belong.addr] = {'static-properties': {},
                                                'cells': {}}

                else:
                    pnfdevs = t_slice.wifi[pnfdev.ALIAS]

                    if pnfdev.addr not in pnfdevs:
                        pnfdevs[belong.addr] = {'static-properties': {},
                                                'blocks': {}}

                pnfdevs[belong.addr]['static-properties'] = \
                        json.loads(belong.properties)

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

    def to_dict(self):
        """ Return a dict representation of the object. """

        out = {}
        out['port'] = self.port
        return out

    def add_pnfdev(self, addr, label):
        """Add PNFDev."""

        if addr in self.pnfdevs:
            raise ValueError("Device address %s already present" % addr)

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
