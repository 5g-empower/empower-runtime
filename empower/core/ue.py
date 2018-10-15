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

import time

from empower.core.cellpool import Cell
from empower.core.cellpool import CellPool

import empower.logger

# add ue message sent, status received
PROCESS_RUNNING = "running"

# del ue message(s) sent, no status(es) received - ho
PROCESS_REMOVING = "removing"

# desconnection ue message received from the enb
PROCESS_DISCONNECTING = "disconnecting"

# UE states at the eNB
INVALID = 0x00
RADIO_CONNECT = 0x01
RADIO_DISCONNECT = 0x02
RRC_IDLE = 0x03
RRC_CONNECT = 0x04

UE_REPORT_STATES = {
    INVALID: "invalid",
    RADIO_CONNECT: "running",
    RADIO_DISCONNECT: "disconnecting",
    RRC_IDLE: "rrc_idle",
    RRC_CONNECT: "rrc_connect"
}


class UE:
    """User Equipment."""

    def __init__(self, ue_id, rnti, imsi, timsi, cell, tenant):

        # read only parameters
        self.ue_id = ue_id
        self.tenant = tenant

        # set on different situations, e.g. after an handover
        self.rnti = rnti

        # imsi
        self.imsi = imsi

        # temporal imsi
        self.timsi = timsi

        # the current cell
        self._cell = cell

        # the ue state
        self._state = PROCESS_RUNNING

        # target cell to be used for handover
        self.target_cell = None

        # migration sats
        self._timer = None

        # the ue measurements, this is set by a ue_measurement module
        self.ue_measurements = {}

        # logger :)
        self.log = empower.logger.get_logger()

    def handle_ue_handover_response(self, origin_vbs, target_vbs, origin_rnti,
                                    target_rnti, origin_pci, target_pci,
                                    opcode):
        """Received as result of a del lvap command."""

        if self.state != PROCESS_REMOVING:
            self.log.error("UE Handover response received in state %s",
                           self.state)
            return

        self.log.info("UE %s handover opcode %u %s (%u) -> %s (%u)",
                      self.ue_id, opcode, origin_vbs.addr, origin_pci,
                      target_vbs.addr, target_pci)

        # handover was a success
        if opcode == 1:

            # set new cell and rnti
            self._cell = target_vbs.cells[target_pci]
            self.rnti = target_rnti

            # set state to running
            self._state = PROCESS_RUNNING

            return

        # handover failed at the source
        if origin_vbs == target_vbs:

            # reset new cell and rnti
            self._cell = origin_vbs.cells[target_pci]
            self.rnti = origin_rnti

            # set state to running
            self._state = PROCESS_RUNNING

            return

    def is_running(self):
        """Check if the UE is running."""

        return self._state == PROCESS_RUNNING

    @property
    def state(self):
        """Return the state."""

        return self._state

    @state.setter
    def state(self, state):
        """Set the CPP."""

        self.log.info("UE %s transition %s->%s", self.ue_id, self.state, state)

        if self.state:
            method = "_%s_%s" % (self.state, state)
        else:
            method = "_none_%s" % state

        if hasattr(self, method):
            callback = getattr(self, method)
            callback()
            return

        raise IOError("Invalid transistion %s -> %s" % (self.state, state))

    def _removing_running(self):

        # set new state
        self._state = PROCESS_RUNNING

        # compute stats
        delta = int((time.time() - self._timer) * 1000)
        self._timer = None
        self.log.info("UE %s handover took %sms", self.ue_id, delta)

    def _running_removing(self):

        # set timer
        self._timer = time.time()

        # set new state
        self._state = PROCESS_REMOVING

        # send ho request message
        self.vbs.connection.send_ue_ho_request(self, self.target_cell)

    def _running_disconnecting(self):

        self._state = PROCESS_DISCONNECTING

        from empower.main import RUNTIME

        # remove UE from the RUNTIME
        RUNTIME.remove_ue(self.ue_id)

    @property
    def cell(self):
        """Get the cell."""

        return self._cell

    @cell.setter
    def cell(self, cell):
        """ Set the cell. """

        if self.state != PROCESS_RUNNING:
            raise ValueError("Handover in progress")

        if not cell:
            return

        if isinstance(cell, CellPool):
            cell = cell[0]

        if not isinstance(cell, Cell):
            raise TypeError("Invalid type: %s" % type(cell))

        # save target block
        self.target_cell = cell

        if self.state == PROCESS_RUNNING:
            self.state = PROCESS_REMOVING
        else:
            IOError("Setting blocks on invalid state: %s" % self.state)

    @property
    def vbs(self):
        """Get the VBS."""

        return self.cell.vbs

    @vbs.setter
    def vbs(self, vbs):
        """ Set the vbs. """

        self.cell = vbs.cells().first()

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the UE """

        ue_meas = {str(k): v for k, v in self.ue_measurements.items()}

        return {'ue_id': self.ue_id,
                'rnti': self.rnti,
                'imsi': self.imsi,
                'timsi': self.timsi,
                'tenant_id': self.tenant.tenant_id,
                'plmn_id': self.tenant.plmn_id,
                'cell': self.cell,
                'vbs': self.vbs,
                'state': self.state,
                'ue_measurements': ue_meas}

    def __str__(self):
        """Return string representation."""

        return "UE %s (%u) @ %s" % (self.ue_id, self.rnti, self.cell)

    def __hash__(self):
        return hash(self.ue_id)

    def __eq__(self, other):
        if isinstance(other, UE):
            return self.ue_id == other.ue_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
