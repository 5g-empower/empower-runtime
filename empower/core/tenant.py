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

from empower.persistence.persistence import TblBelongs
from empower.persistence import Session
from empower.datatypes.etheraddress import EtherAddress
from empower.core.utils import ofmatch_d2s
from empower.core.utils import ofmatch_s2d

T_TYPE_SHARED = "shared"
T_TYPE_UNIQUE = "unique"
T_TYPES = [T_TYPE_SHARED, T_TYPE_UNIQUE]


class TrafficRuleProp(dict):
    """Maps Flows to TrafficRules."""

    def __init__(self, tenant, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__uuids__ = {}
        self.tenant = tenant

    def __getitem__(self, key):

        key = ofmatch_d2s(ofmatch_s2d(key))

        try:
            return dict.__getitem__(self, key)
        except KeyError:
            value = TrafficRule(self.tenant, 0, 1500, False)
            dict.__setitem__(self, key, value)
            return dict.__getitem__(self, key)

    def __delitem__(self, key):
        """Clear traffic rule configuration."""

        key = ofmatch_d2s(ofmatch_s2d(key))

        value = self.__getitem__(key)

        # remove queues
        from empower.main import RUNTIME
        from empower.intentserver.intentserver import IntentServer
        intent_server = RUNTIME.components[IntentServer.__module__]

        wtps = RUNTIME.tenants[value.tenant.tenant_id].wtps.values()

        for wtp in wtps:

            if not wtp.is_online():
                continue

            # delete queue on wtp
            for block in wtp.supports:
                wtp.connection.send_del_traffic_rule(block, value)
                del block.queues[(value.tenant.tenant_name, value.dscp)]

        # remove traffic rules
        if key in self.__uuids__:
            for uuid in self.__uuids__[key]:
                intent_server.remove_rule(uuid)
            del self.__uuids__[key]

        # remove old entry
        dict.__delitem__(self, key)

    def __setitem__(self, key, value):
        """Set traffic rule configuration."""

        key = ofmatch_d2s(ofmatch_s2d(key))

        if value and not isinstance(value, TrafficRule):
            raise KeyError("Expected TrafficRule, got %s" % type(key))

        # remove traffic rule
        if self.__contains__(key):
            self.__delitem__(key)

        self.__uuids__[key] = []

        from empower.main import RUNTIME
        from empower.intentserver.intentserver import IntentServer
        intent_server = RUNTIME.components[IntentServer.__module__]

        wtps = RUNTIME.tenants[value.tenant.tenant_id].wtps.values()

        for wtp in wtps:

            if not wtp.is_online():
                continue

            # get network port
            port = wtp.port()

            # set/update traffic rule
            intent = {'version': '1.0',
                      'dpid': port.dpid,
                      'port': port.port_id,
                      'dscp': value.dscp,
                      'match': ofmatch_s2d(key)}

            # add new virtual link
            uuid = intent_server.add_traffic_rule(intent)
            self.__uuids__[key].append(uuid)

            # create queues on wtp
            for block in wtp.supports:
                wtp.connection.send_set_traffic_rule(block, value)

        # add entry
        dict.__setitem__(self, key, value)


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
        traffic_rules: dictionary mapping dscp values to traffic rules. 0 is
            the default traffic rule created when the WTP connects.
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
               'traffic_rules']

    def __init__(self, tenant_id, tenant_name, owner, desc, bssid_type,
                 plmn_id=None):

        self.tenant_id = tenant_id
        self.plmn_id = plmn_id
        self.tenant_name = tenant_name
        self.owner = owner
        self.desc = desc
        self.bssid_type = bssid_type
        self.wtps = {}
        self.cpps = {}
        self.vbses = {}
        self.lvaps = {}
        self.ues = {}
        self.lvnfs = {}
        self.vaps = {}
        self.components = {}
        self.traffic_rules = TrafficRuleProp(self)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Poll """

        out = {}

        for field in self.TO_DICT:
            attr = getattr(self, field)
            if type(attr) is dict:
                out[field] = {str(k): v for k, v in attr.items()}
            else:
                out[field] = attr

        return out

    def get_prefix(self):
        """Return tenant prefix."""

        tokens = [self.tenant_id.hex[0:12][i:i + 2] for i in range(0, 12, 2)]
        return EtherAddress(':'.join(tokens))

    def add_pnfdev(self, pnfdev):
        """Add a new PNF Dev to the Tenant.

        Args:
            pnfdev, a PNFDev object

        Returns:
            None

        Raises:
            KeyError, if the pnfdev is not available
        """

        pnfdevs = getattr(self, pnfdev.ALIAS)

        if pnfdev.addr in pnfdevs:
            return

        pnfdevs[pnfdev.addr] = pnfdev

        belongs = TblBelongs(tenant_id=self.tenant_id, addr=pnfdev.addr)

        session = Session()
        session.add(belongs)
        session.commit()

    def remove_pnfdev(self, pnfdev):
        """Remove a PNFDev from the Tenant.

        Args:
            addr, a PNFDev object

        Returns:
            None
        Raises:
            KeyError, if the pnfdev is not available
        """

        pnfdevs = getattr(self, pnfdev.ALIAS)

        if pnfdev.addr not in pnfdevs:
            return

        del pnfdevs[pnfdev.addr]

        belongs = Session().query(TblBelongs) \
                           .filter(TblBelongs.tenant_id == self.tenant_id,
                                   TblBelongs.addr == pnfdev.addr) \
                           .first()

        session = Session()
        session.delete(belongs)
        session.commit()

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
