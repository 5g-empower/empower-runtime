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


class UE:
    """User Equipment."""

    def __init__(self, imsi, rnti, cell, plmn_id, tenant):

        self.imsi = imsi
        self.rnti = rnti
        self.plmn_id = plmn_id
        self._cell = cell
        self.tenant = tenant

    @property
    def cell(self):
        """Get the cell."""

        return self._cell

    @cell.setter
    def cell(self, cell):
        """ Set the cell. """

        if self._cell == cell:
            return

        # perform handover

    @property
    def vbs(self):
        """Get the VBS."""

        return self.cell.vbs

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the UE """

        return {'imsi': self.imsi,
                'rnti': self.rnti,
                'plmn_id': self.plmn_id,
                'cell': self.cell,
                'vbs': self.vbs}

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, UE):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
