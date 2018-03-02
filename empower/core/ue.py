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

import empower.logger

# ue is active
UE_ACTIVE = "active"

# ho in progress
UE_HO_IN_PROGRESS = "ho_in_progress"


class UE:
    """User Equipment."""

    def __init__(self, ue_id, imsi, rnti, cell, plmn_id, tenant):

        self.ue_id = ue_id
        self.imsi = imsi
        self.rnti = rnti
        self.plmn_id = plmn_id
        self._cell = cell
        self.tenant = tenant
        self.__state = None
        self.log = empower.logger.get_logger()

    def __str__(self):
        """Return string representation."""

        return "UE %s @ %s" % (self.ue_id, self.cell)

    @property
    def state(self):
        """Return the state."""

        return self.__state

    @state.setter
    def state(self, state):
        """Set the CPP."""

        self.log.info("UE %s transition %s->%s", self.ue_id, self.state,
                      state)

        if self.state:
            method = "_%s_%s" % (self.state, state)
        else:
            method = "_none_%s" % state

        if hasattr(self, method):
            callback = getattr(self, method)
            callback()
            return

        raise IOError("Invalid transistion %s -> %s" % (self.state, state))

    def _none_active(self):

        self.__state = UE_ACTIVE

    def _active_ho_in_progress(self):

        self.__state = UE_HO_IN_PROGRESS

    def _ho_in_progress_active(self):

        self.__state = UE_ACTIVE

    def set_active(self):

        self.state = UE_ACTIVE

    def set_ho_in_progress(self):

        self.state = UE_HO_IN_PROGRESS

    def is_active(self):

        return self.state == UE_ACTIVE

    def is_ho_in_progress(self):

        return self.state == UE_HO_IN_PROGRESS

    @property
    def cell(self):
        """Get the cell."""

        return self._cell

    @cell.setter
    def cell(self, cell):
        """ Set the cell. """

        if self._cell == cell:
            return

        if not cell.vbs.is_online():
            raise ValueError("Cell %s is not online", cell)

        if self.state != UE_ACTIVE:
            raise ValueError("An handover is already in progress")

        # change state
        self.set_ho_in_progress()

        # perform handover
        self.cell.vbs.connection.send_ue_ho_request(self, cell)

    @property
    def vbs(self):
        """Get the VBS."""

        return self.cell.vbs

    @vbs.setter
    def vbs(self, vbs):
        """ Set the vbs. """

        for cell in vbs.cells:
            self.cell = cell
            return

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the UE """

        return {'ue_id': self.ue_id,
                'imsi': self.imsi,
                'rnti': self.rnti,
                'plmn_id': self.plmn_id,
                'cell': self.cell,
                'vbs': self.vbs,
                'state': self.state}

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, UE):
            return self.ue_id == other.ue_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
