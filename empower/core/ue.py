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

# ue ho request send, no ue response received from source cell
UE_HO_IN_PROGRESS_REMOVING = "ho_in_progress_removing"

# ue ho request send, no ue response received from target cell
UE_HO_IN_PROGRESS_ADDING = "ho_in_progress_adding"


class UE:
    """User Equipment."""

    def __init__(self, imsi, rnti, cell, plmn_id, tenant):

        self.imsi = imsi
        self.rnti = rnti
        self.plmn_id = plmn_id
        self._cell = cell
        self.tenant = tenant
        self.__state = None
        self.log = empower.logger.get_logger()

    @property
    def state(self):
        """Return the state."""

        return self.__state

    @state.setter
    def state(self, state):
        """Set the CPP."""

        self.log.info("UE %s transition %s->%s", self.imsi, self.state,
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

    def _active_ho_in_progress_removing(self):

        self.__state = UE_HO_IN_PROGRESS_REMOVING

    def _ho_in_progress_removing_active(self):

        self.__state = UE_ACTIVE

    def _ho_in_progress_removing_ho_in_progress_adding(self):

        self.__state = UE_HO_IN_PROGRESS_ADDING

    def _ho_in_progress_adding_active(self):

        self.__state = UE_ACTIVE

    def set_active(self):

        self.state = UE_ACTIVE

    def set_ho_in_progress_removing(self):

        self.state = UE_HO_IN_PROGRESS_REMOVING

    def set_ho_in_progress_adding(self):

        self.state = UE_HO_IN_PROGRESS_ADDING

    def is_ative(self):

        return self.state == UE_ACTIVE

    def is_ho_in_progress_removing(self):

        return self.state == UE_HO_IN_PROGRESS_REMOVING

    def is_ho_in_progress_adding(self):

        return self.state == UE_HO_IN_PROGRESS_ADDING

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
        self.set_ho_in_progress_removing()

        # perform handover
        self.cell.vbs.connection.send_ue_ho_request(self, cell)

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
                'vbs': self.vbs,
                'state': self.state}

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, UE):
            return self.imsi == other.imsi
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
