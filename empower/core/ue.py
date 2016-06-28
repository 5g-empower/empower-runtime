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

"""(VBSP) User Equipment class."""

from empower.datatypes.etheraddress import EtherAddress


import empower.logger
LOG = empower.logger.get_logger()


def rnti_to_ether(rnti):
    """Convert RNTU to EtherAddress."""

    str_hex_value = format(rnti, 'x')
    padding = '0' * (12 - len(str_hex_value))
    mac_string = padding + str_hex_value
    mac_string_array = \
        [mac_string[i:i+2] for i in range(0, len(mac_string), 2)]

    return EtherAddress(":".join(mac_string_array))


class UE(object):
    """User Equipment."""

    def __init__(self, rnti, vbsp, config, capabilities):

        self.rnti = rnti
        self.ue_id = rnti_to_ether(self.rnti)
        self.vbsp = vbsp
        self.config = config
        self.capabilities = capabilities
        self.rrc_measurements_config = {}
        self.rrc_measurements = {}
        self.pcell_rsrp = None
        self.pcell_rsrq = None

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the LVAP """

        return {'rnti': self.rnti,
                'vbsp': self.vbsp.addr,
                'ue_id': self.ue_id,
                'capabilities': self.capabilities,
                'rrc_measurements_config': self.rrc_measurements_config}

    def __eq__(self, other):
        if isinstance(other, UE):
            return self.rnti == other.rnti
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
