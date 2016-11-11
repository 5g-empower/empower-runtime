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


class UE(object):
    """User Equipment."""

    def __init__(self, rnti, vbs):

        self.rnti = rnti
        self.imsi = None
        self.plmn_id = None
        self.mac_addr = None
        self.ue_id = hex_to_ether(self.rnti)
        self.vbs = vbs
        self.rrc_state = None
        self.capabilities = {}
        self.rrc_meas_config = {}
        self.rrc_meas = {}
        self.pcell_rsrp = None
        self.pcell_rsrq = None

        self.vbs.connection.send_rrc_meas_conf_req(self)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the UE """

        return {'rnti': self.rnti,
                'imsi': self.imsi,
                'plmn_id': self.plmn_id,
                'vbs': self.vbs.addr,
                'ue_id': self.ue_id,
                'rrc_state': self.rrc_state,
                'capabilities': self.capabilities,
                'rrc_meas_config': self.rrc_meas_config,
                'rrc_meas': self.rrc_meas,
                'primary_cell_rsrp': self.pcell_rsrp,
                'primary_cell_rsrq': self.pcell_rsrq}

    def __eq__(self, other):

        if isinstance(other, UE):
            return self.rnti == other.rnti

        return False

    def __ne__(self, other):

        return not self.__eq__(other)


