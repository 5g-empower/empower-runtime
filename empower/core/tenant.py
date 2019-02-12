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

"""EmPOWER Runtime Tenant Class."""

import json

from sqlalchemy.exc import IntegrityError

from empower.persistence.persistence import TblSlice
from empower.persistence.persistence import TblSliceBelongs
from empower.persistence.persistence import TblTrafficRule
from empower.core.slice import Slice
from empower.persistence import Session
from empower.core.utils import get_module
from empower.datatypes.etheraddress import EtherAddress
from empower.core.trafficrule import TrafficRule
from empower.vbsp import EP_OPERATION_SET
from empower.vbsp import EP_OPERATION_ADD

T_TYPE_SHARED = "shared"
T_TYPE_UNIQUE = "unique"
T_TYPES = [T_TYPE_SHARED, T_TYPE_UNIQUE]


class Tenant:
    """Tenant object representing a network slice.

    This represents basically a virtual network or slice requested and managed
    by a certain tenant. You can imagine a Tenant as a slice of the network.
    Each Tenant can be accessed using the Controller REST interface.

    Attributes:
        tenant_id: The tenant identifier
        owner: The username of the user that requested this pool
        desc: Human readable description
        bssid_type: shared (VAP) or unique (LVAP)
    """

    TO_DICT = ['tenant_id',
               'tenant_name',
               'plmn_id',
               'owner',
               'desc',
               'bssid_type',
               'lvaps',
               'ues',
               'lvnfs',
               'wtps',
               'cpps',
               'vbses',
               'components',
               'slices',
               'endpoints',
               'traffic_rules']

    def __init__(self, tenant_id, tenant_name, owner, desc, bssid_type,
                 plmn_id=None):

        self.tenant_id = tenant_id
        self.plmn_id = plmn_id
        self.tenant_name = tenant_name
        self.owner = owner
        self.desc = desc
        self.bssid_type = bssid_type
        self.endpoints = {}
        self.lvaps = {}
        self.ues = {}
        self.lvnfs = {}
        self.vaps = {}
        self.slices = {}
        self.components = {}

    @property
    def wtps(self):
        """Return WTPs. """

        from empower.main import RUNTIME

        return RUNTIME.wtps

    @property
    def cpps(self):
        """Return CPPs. """

        from empower.main import RUNTIME

        return RUNTIME.cpps

    @property
    def vbses(self):
        """Return VBSes. """

        from empower.main import RUNTIME

        return RUNTIME.vbses

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Poll """

        out = {}

        for field in self.TO_DICT:
            attr = getattr(self, field)
            if isinstance(attr, dict):
                out[field] = {str(k): v for k, v in attr.items()}
            else:
                out[field] = attr

        return out

    def get_prefix(self):
        """Return tenant prefix."""

        tokens = [self.tenant_id.hex[0:12][i:i + 2] for i in range(0, 12, 2)]
        return EtherAddress(':'.join(tokens))

    def generate_bssid(self, mac):
        """ Generate a new BSSID address. """

        base_mac = self.get_prefix()

        base = str(base_mac).split(":")[0:3]
        unicast_addr_mask = int(base[0], 16) & 0xFE
        base[0] = str(format(unicast_addr_mask, 'X'))
        suffix = str(mac).split(":")[3:6]

        return EtherAddress(":".join(base + suffix))

    def add_endpoint(self, endpoint_id, endpoint_name, datapath, ports):
        """Add Endpoint."""

        from empower.core.endpoint import Endpoint
        from empower.core.virtualport import VirtualPort

        endpoint = Endpoint(uuid=endpoint_id,
                            label=endpoint_name,
                            datapath=datapath)

        for vport_id, vport in ports.items():

            port_id = int(vport['port_id'])
            network_port = datapath.network_ports[port_id]

            virtual_port = VirtualPort(endpoint,
                                       network_port=network_port,
                                       virtual_port_id=int(vport_id))

            virtual_port.dont_learn = vport['properties']['dont_learn']

            endpoint.ports[int(vport_id)] = virtual_port

        self.endpoints[endpoint_id] = endpoint

    def remove_endpoint(self, endpoint_id):
        """Remove Endpoint."""

        if endpoint_id not in self.endpoints:
            raise KeyError(endpoint_id)

        endpoint = self.endpoints[endpoint_id]

        endpoint.ports.clear()
        del self.endpoints[endpoint_id]

    @property
    def traffic_rules(self):
        """Fetch traffic rule queues in this tenant."""

        trs = \
            Session().query(TblTrafficRule) \
                     .filter(TblTrafficRule.tenant_id == self.tenant_id) \
                     .all()

        results = {}

        for rule in trs:
            results[rule.match] = {'match': rule.match,
                                   'label': rule.label,
                                   'priority': rule.priority,
                                   'dscp': rule.dscp}

        return results

    def add_traffic_rule(self, match, dscp, label, priority=0):
        """Add a new traffic rule to the Tenant.

        Args:
            match, a Match object
            dscp, a slice DSCP code
            label, a humand readable description of the rule
        Returns:
            None

        Raises:
            Nones
        """

        trule = TrafficRule(tenant=self,
                            match=match,
                            dscp=dscp,
                            priority=priority,
                            label=label)

        # Send command to IBN
        from empower.ibnp.ibnpserver import IBNPServer
        ibnp_server = get_module(IBNPServer.__module__)
        if ibnp_server:
            ibnp_server.add_traffic_rule(trule)

        rule = TblTrafficRule(tenant_id=self.tenant_id, match=match,
                              dscp=dscp, priority=priority, label=label)

        try:
            session = Session()
            session.add(rule)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise ValueError("Duplicate (%s, %s)" % (self.tenant_id, match))

    def del_traffic_rule(self, match):
        """Delete a traffic rule from this tenant.

        Args:
            match, a Match object

        Returns:
            None

        Raises:
            None
        """

        rule = Session().query(TblTrafficRule) \
                        .filter(TblTrafficRule.tenant_id == self.tenant_id,
                                TblTrafficRule.match == match) \
                        .first()
        if not rule:
            raise KeyError(rule)

        # Send command to IBN
        from empower.ibnp.ibnpserver import IBNPServer
        ibnp_server = get_module(IBNPServer.__module__)
        if ibnp_server:
            ibnp_server.del_traffic_rule(self.tenant_id, match)

        session = Session()
        session.delete(rule)
        session.commit()

    def add_slice(self, dscp, request):
        """Add a new slice to the Tenant.

        Args:
            dscp, a DSCP object
            request, the slice descriptor in json format

        Returns:
            None

        Raises:
            ValueError, if the dscp is not valid
        """

        # create new instance
        slc = Slice(dscp, self, request)

        # descriptors has been parsed, now it is safe to write to the db
        try:

            session = Session()

            tbl_slc = TblSlice(tenant_id=self.tenant_id,
                               dscp=slc.dscp,
                               wifi=json.dumps(slc.wifi['static-properties']),
                               lte=json.dumps(slc.lte['static-properties']))

            session.add(tbl_slc)

            for wtp_addr in slc.wifi['wtps']:

                properties = \
                    json.dumps(slc.wifi['wtps'][wtp_addr]['static-properties'])

                belongs = TblSliceBelongs(tenant_id=self.tenant_id,
                                          dscp=tbl_slc.dscp,
                                          addr=wtp_addr,
                                          properties=properties)

                session.add(belongs)

            for vbs_addr in slc.lte['vbses']:

                properties = \
                    json.dumps(slc.lte['vbses'][vbs_addr]['static-properties'])

                belongs = TblSliceBelongs(tenant_id=self.tenant_id,
                                          dscp=tbl_slc.dscp,
                                          addr=vbs_addr,
                                          properties=properties)

                session.add(belongs)

            session.commit()

        except IntegrityError:
            session.rollback()
            raise ValueError()

        # store slice
        self.slices[dscp] = slc

        # create slice on WTPs
        for wtp_addr in self.wtps:

            wtp = self.wtps[wtp_addr]

            if not wtp.is_online():
                continue

            for block in wtp.supports:
                wtp.connection.send_set_slice(block, slc)

        # create slice on VBSes
        for vbs_addr in self.vbses:

            vbs = self.vbses[vbs_addr]

            if not vbs.is_online():
                continue

            for cell in vbs.cells.values():
                vbs.connection.\
                    send_add_set_ran_mac_slice_request(cell,
                                                       slc,
                                                       EP_OPERATION_ADD)

    def set_slice(self, dscp, request):
        """Update a slice in the Tenant.

        Args:
            dscp, a DSCP object
            request, the slice descriptor in json format

        Returns:
            None

        Raises:
            ValueError, if the dscp is not valid
        """

        # create new instance
        slc = Slice(dscp, self, request)
        tenant_id = self.tenant_id

        # update db
        try:

            session = Session()

            tbl_slice = Session().query(TblSlice) \
                                 .filter(TblSlice.tenant_id == tenant_id) \
                                 .filter(TblSlice.dscp == slc.dscp) \
                                 .first()

            tbl_slice.wifi = json.dumps(slc.wifi['static-properties'])
            tbl_slice.lte = json.dumps(slc.lte['static-properties'])

            for wtp_addr in slc.wifi['wtps']:

                properties = \
                    json.dumps(slc.wifi['wtps'][wtp_addr]['static-properties'])

                tbl_belongs = \
                    Session().query(TblSliceBelongs) \
                             .filter(TblSliceBelongs.tenant_id == tenant_id) \
                             .filter(TblSliceBelongs.dscp == slc.dscp) \
                             .filter(TblSliceBelongs.addr == wtp_addr) \
                             .first()

                if not tbl_belongs:

                    belongs = TblSliceBelongs(tenant_id=self.tenant_id,
                                              dscp=slc.dscp,
                                              addr=wtp_addr,
                                              properties=properties)

                    session.add(belongs)

                else:

                    tbl_belongs.properties = properties

            for vbs_addr in slc.lte['vbses']:

                properties = \
                    json.dumps(slc.lte['vbses'][vbs_addr]['static-properties'])

                tbl_belongs = \
                    Session().query(TblSliceBelongs) \
                             .filter(TblSliceBelongs.tenant_id == tenant_id) \
                             .filter(TblSliceBelongs.dscp == slc.dscp) \
                             .filter(TblSliceBelongs.addr == vbs_addr) \
                             .first()

                if not tbl_belongs:

                    belongs = TblSliceBelongs(tenant_id=self.tenant_id,
                                              dscp=slc.dscp,
                                              addr=vbs_addr,
                                              properties=properties)

                    session.add(belongs)

                else:

                    tbl_belongs.properties = properties

            session.commit()

        except IntegrityError:
            session.rollback()
            raise ValueError()

        # store slice
        self.slices[dscp] = slc

        # create slice on WTPs
        for wtp_addr in self.wtps:

            wtp = self.wtps[wtp_addr]

            if not wtp.is_online():
                continue

            for block in wtp.supports:
                wtp.connection.send_set_slice(block, slc)

        # create slice on VBSes
        for vbs_addr in self.vbses:

            vbs = self.vbses[vbs_addr]

            if not vbs.is_online():
                continue

            current_rntis = []

            # The UEs in the slice must be confirmed

            for ue in list(self.ues.values()):

                if vbs == ue.vbs and dscp == ue.slice:
                    current_rntis.append(ue.rnti)

            for cell in vbs.cells.values():
                vbs.connection.\
                    send_add_set_ran_mac_slice_request(cell,
                                                       slc,
                                                       EP_OPERATION_SET,
                                                       current_rntis)

    def del_slice(self, dscp):
        """Del slice from.

        Args:
            dscp, a DSCP object

        Returns:
            None

        Raises:
            ValueError, if the dscp is not valid
        """

        # fetch slice
        slc = self.slices[dscp]
        tenant_id = self.tenant_id

        # delete it from the db
        try:

            session = Session()

            rem = Session().query(TblSlice) \
                           .filter(TblSlice.tenant_id == self.tenant_id) \
                           .filter(TblSlice.dscp == dscp) \
                           .first()

            session.delete(rem)

            for wtp_addr in slc.wifi['wtps']:

                rem = \
                    Session().query(TblSliceBelongs) \
                             .filter(TblSliceBelongs.tenant_id == tenant_id) \
                             .filter(TblSliceBelongs.dscp == slc.dscp) \
                             .filter(TblSliceBelongs.addr == wtp_addr) \
                             .first()

                if rem:
                    session.delete(rem)

            for vbs_addr in slc.lte['vbses']:

                rem = \
                    Session().query(TblSliceBelongs) \
                             .filter(TblSliceBelongs.tenant_id == tenant_id) \
                             .filter(TblSliceBelongs.dscp == slc.dscp) \
                             .filter(TblSliceBelongs.addr == vbs_addr) \
                             .first()

                if rem:
                    session.delete(rem)

            session.commit()

        except IntegrityError:
            session.rollback()
            raise ValueError()

        # delete it from the WTPs
        for wtp_addr in self.wtps:

            wtp = self.wtps[wtp_addr]

            if not wtp.is_online():
                continue

            for block in wtp.supports:
                wtp.connection.send_del_slice(block, self.tenant_name, dscp)

        # delete it from the VBSes
        for vbs_addr in self.vbses:

            vbs = self.vbses[vbs_addr]

            if not vbs.is_online():
                continue

            for cell in vbs.cells.values():
                vbs.connection.send_del_ran_mac_slice_request(cell,
                                                              self.plmn_id,
                                                              dscp)

        # remove slice
        del self.slices[dscp]

    def __str__(self):
        return str(self.tenant_id)

    def __hash__(self):
        return hash(self.tenant_id)

    def __eq__(self, other):
        if isinstance(other, Tenant):
            return self.tenant_id == other.tenant_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
