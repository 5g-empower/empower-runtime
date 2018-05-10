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

"""Endpoints Server."""

from empower.restserver.restserver import RESTServer
from empower.datatypes.etheraddress import EtherAddress
from empower.core.endpoint import Endpoint
from empower.core.networkport import NetworkPort
from empower.core.virtualport import VirtualPort
from empower.persistence.persistence import TblEndpoint, TblVirtualPort
from empower.persistence import Session
from empower.endpoint.tenantendpointhandler import TenantEndpointHandler
from empower.endpoint.tenantendpointporthandler import TenantEndpointPortHandler
from empower.endpoint.tenantendpointnexthandler import TenantEndpointNextHandler

from empower.main import RUNTIME


class EndpointServer:
    """Exposes the EmPOWER Endpoint API."""

    handlers = [TenantEndpointHandler]

    def __init__(self):

        self.__load_endpoints()
        self.__load_vports()

    @property
    def endpoints(self):
        """Return Endpoints."""

        return getattr(RUNTIME, 'endpoints')

    def __load_endpoints(self):
        """Load PNFDevs."""

        endpoints = Session().query(TblEndpoint).all()

        for endpoint_db in endpoints:

            endpoint = Endpoint(endpoint_db.endpoint_id,
                                endpoint_db.endpoint_name,
                                endpoint_db.desc)

            tenant = RUNTIME.tenants[endpoint_db.tenant_id]
            tenant.endpoints[endpoint_db.endpoint_id] = endpoint

            self.endpoints[endpoint_db.endpoint_id] = endpoint

    def __load_vports(self):

        vports = Session().query(TblVirtualPort).all()

        for vport in vports:

            net_port = NetworkPort(vport.dpid,
                                   port_id=vport.port_id,
                                   hwaddr=vport.hwaddr,
                                   iface=vport.iface)

            virtual_port = VirtualPort(vport.endpoint_id,
                                       network_port=net_port,
                                       virtual_port_id=vport.vport_id,
                                       learn_host=vport.learn_host)

            parent_endpoint = self.endpoints[vport.endpoint_id]
            parent_endpoint.ports[vport.vport_id] = virtual_port

    def add_endpoint(self, endpoint_id, tenant_id, endpoint_name, desc, ports):
        """Add Endpoint."""

        endpoint = Endpoint(endpoint_id, endpoint_name, desc)

        for vport_id, vport in ports.items():

            net_port = NetworkPort(dpid=EtherAddress(vport['dpid']),
                                   port_id=int(vport['port_id']),
                                   hwaddr=EtherAddress(vport['hwaddr']),
                                   iface=vport['iface'])

            virtual_port = VirtualPort(endpoint_id,
                                       network_port=net_port,
                                       virtual_port_id=int(vport_id),
                                       learn_host=bool(vport['learn_host']))

            endpoint.ports[int(vport_id)] = virtual_port

        if tenant_id not in RUNTIME.tenants:
            raise KeyError(tenant_id)

        tenant = RUNTIME.tenants[tenant_id]
        tenant.endpoints[endpoint_id] = endpoint
        self.endpoints[endpoint_id] = endpoint

        session = Session()
        session.add(TblEndpoint(endpoint_id=endpoint_id,
                                tenant_id=tenant_id,
                                endpoint_name=endpoint_name,
                                desc=desc))
        session.commit()

        session = Session()

        for vport_id, vport in endpoint.ports.items():

            session.add(TblVirtualPort(endpoint_id=endpoint_id,
                                       vport_id=vport_id,
                                       dpid=vport.network_port.dpid,
                                       port_id=vport.network_port.port_id,
                                       iface=vport.network_port.iface,
                                       hwaddr=vport.network_port.hwaddr,
                                       learn_host=vport.learn_host))
        session.commit()

    def remove_endpoint(self, endpoint_id, tenant_id):
        """Remove Endpoint."""

        if endpoint_id not in self.endpoints:
            raise KeyError(endpoint_id)

        endpoint = self.endpoints[endpoint_id]

        del RUNTIME.tenants[tenant_id].endpoints[endpoint_id]
        del self.endpoints[endpoint_id]

        session = Session()

        for i in range(0, len(endpoint.ports)):

            vport_db = Session().query(TblVirtualPort) \
                .filter(TblVirtualPort.endpoint_id == endpoint_id) \
                .first()

            session.delete(vport_db)

        session.commit()

        endpoint.ports.clear()

        endpoint_db = Session().query(TblEndpoint) \
            .filter(TblEndpoint.endpoint_id == endpoint_id) \
            .first()

        session = Session()
        session.delete(endpoint_db)
        session.commit()


def launch():
    """Start Endpoint Server Module. """

    server = EndpointServer()

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(TenantEndpointHandler, server)
    rest_server.add_handler_class(TenantEndpointPortHandler, server)
    rest_server.add_handler_class(TenantEndpointNextHandler, server)

    return server
