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

from empower.persistence.persistence import TblBelongs
from empower.persistence.persistence import TblTrafficRuleQueue
from empower.persistence import Session
from empower.datatypes.etheraddress import EtherAddress
from empower.core.utils import ofmatch_d2s
from empower.core.utils import ofmatch_s2d
from empower.core.trafficrulequeue import TrafficRuleQueue


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
               'components']

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
        self.endpoints = {}
        self.lvaps = {}
        self.ues = {}
        self.lvnfs = {}
        self.vaps = {}
        self.components = {}

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

    def get_traffic_rule_queues(self):
        """Fetch traffic rule queues in this tenant."""

        trqs = \
            Session().query(TblTrafficRuleQueue) \
                     .filter(TblTrafficRuleQueue.tenant_id == self.tenant_id) \
                     .all()

        results = {}

        for trq in trqs:
            amsdu_aggregation = trq.amsdu_aggregation
            results[trq.dscp] = {'quantum': trq.quantum,
                                 'amsdu_aggregation': amsdu_aggregation}

        return results

    def add_traffic_rule_queue(self, dscp, quantum, amsdu_aggregation):
        """Add a new TRQ to the Tenant.

        Args:
            dscp, a DSCP object
            quatum, the quanum in usec
            aggregaion, enabled/disable aggregation

        Returns:
            None

        Raises:
            ValueError, if the dscp is not valid
        """

        amsdu_aggregation = json.loads(amsdu_aggregation.lower())

        trq = TblTrafficRuleQueue(tenant_id=self.tenant_id,
                                  dscp=dscp,
                                  quantum=int(quantum),
                                  amsdu_aggregation=amsdu_aggregation)

        try:
            session = Session()
            session.add(trq)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise ValueError("Duplicate entry (%s, %s)", self.tenant_id, dscp)

        self.dispach_traffic_rule(dscp)

    def set_traffic_rule_queue(self, dscp, quantum, amsdu_aggregation):
        """Add a new TRQ to the Tenant.

        Args:
            dscp, a DSCP object
            quatum, the quanum in usec
            aggregaion, enabled/disable aggregation

        Returns:
            None

        Raises:
            ValueError, if the dscp is not valid
        """

        trq = Session().query(TblTrafficRuleQueue) \
                       .filter(TblTrafficRuleQueue.dscp == dscp) \
                       .first()
        if not trq:
            raise KeyError(dscp)

        session = Session()

        trq.quantum = quantum
        trq.amsdu_aggregation = amsdu_aggregation

        session.commit()

        self.dispach_traffic_rule(dscp)

    def dispach_traffic_rule(self, dscp):

        trq = Session().query(TblTrafficRuleQueue) \
                       .filter(TblBelongs.tenant_id == self.tenant_id,
                               TblTrafficRuleQueue.dscp == dscp) \
                       .first()

        for wtp in self.wtps.values():

            for block in wtp.supports:

                msg = \
                    TrafficRuleQueue(ssid=self.tenant_name,
                                     dscp=trq.dscp,
                                     block=block,
                                     quantum=trq.quantum,
                                     amsdu_aggregation=trq.amsdu_aggregation)

                block.radio.connection.send_set_traffic_rule_queue(msg)

    def del_traffic_rule_queue(self, dscp):
        """Add a new TRQ to the Tenant.

        Args:
            dscp, a DSCP object

        Returns:
            None

        Raises:
            ValueError, if the dscp is not valid
        """

        trq = Session().query(TblTrafficRuleQueue) \
                       .filter(TblBelongs.tenant_id == self.tenant_id,
                               TblTrafficRuleQueue.dscp == dscp) \
                       .first()
        if not trq:
            raise KeyError(dscp)

        for wtp in self.wtps.values():
            for block in wtp.supports:
                msg = \
                    TrafficRuleQueue(ssid=self.tenant_name,
                                     dscp=trq.dscp,
                                     block=block,
                                     quantum=trq.quantum,
                                     amsdu_aggregation=trq.amsdu_aggregation)
                block.radio.connection.send_del_traffic_rule_queue(msg)

        session = Session()
        session.delete(trq)
        session.commit()

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
