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

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class UE(object):
    """User Equipment."""

    def __init__(self, pci, plmn_id, rnti, imsi, tenant, vbs):

        self.pci = pci
        self.plmn_id = plmn_id
        self.rnti = rnti
        self.imsi = imsi
        self.vbs = vbs
        self.tenant = tenant

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the UE """

        return {'rnti': self.rnti,
                'plmn_id': self.plmn_id,
                'imsi': self.imsi,
                'vbs': self.vbs,
                'pci': self.pci}

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, UE):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
