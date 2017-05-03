#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio, Supreeth Herle
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

"""User Equipment class."""

from empower.core.utils import hex_to_ether

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class UE(object):
    """User Equipment."""

    def __init__(self, addr, rnti, vbs):

        self.addr = addr
        self.rnti = rnti
        self.imsi = None
        self.vbs = vbs
        self._tenant = None
        self.rrc_state = None
        self.capabilities = {}
        self.rrc_meas_config = {}
        self.rrc_meas = {}
        self.pcell_rsrp = None
        self.pcell_rsrq = None

    @property
    def plmn_id(self):
        """Get the plmn_id."""

        return self.tenant.plmn_id if self.tenant else None

    @property
    def tenant(self):
        """ Get the tenant assigned to this UE. """

        return self._tenant

    @tenant.setter
    def tenant(self, tenant):
        """ Set the tenant. """

        if self._tenant == tenant:
            return

        if self.tenant:

            LOG.info("Removing %s from PLMN id %s", self.addr, self.plmn_id)

            self._tenant = None
            del self._tenant.ues[self.addr]

            # Raise UE leave
            self.vbs.connection.server.send_ue_leave_message_to_self(self)

            return

        if not tenant:
            return

        LOG.info("Adding UE %s to PLMN id %s", self.addr, tenant.plmn_id)

        self._tenant = tenant
        self._tenant.ues[self.addr] = self

        # Raise UE join
        self.vbs.connection.server.send_ue_join_message_to_self(self)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the UE """

        return {'addr': self.addr,
                'rnti': self.rnti,
                'plmn_id': self.plmn_id,
                'imsi': self.imsi,
                'vbs': self.vbs,
                'rrc_state': self.rrc_state,
                'capabilities': self.capabilities,
                'rrc_meas_config': self.rrc_meas_config,
                'rrc_meas': self.rrc_meas,
                'primary_cell_rsrp': self.pcell_rsrp,
                'primary_cell_rsrq': self.pcell_rsrq}

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, UE):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
