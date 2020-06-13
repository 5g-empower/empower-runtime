#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""User Equipment."""

from empower_core.serialize import serializable_dict

USER_STATUS_CONNECTED = 1
USER_STATUS_DISCONNECTED = 2

USER_STATUS = {
    USER_STATUS_CONNECTED: "connected",
    USER_STATUS_DISCONNECTED: "disconnected"
}


@serializable_dict
class User():
    """User Equipment

    Attributes:
        imsi: the UE IMSI
        tmsi: the UE TMSI
        rnti: the UE RNTI
        status: the status of the UE (1=connected, 2=disconnected)
    """

    def __init__(self, imsi, tmsi, rnti, cell, status):
        self.imsi = imsi
        self.tmsi = tmsi
        self.rnti = rnti
        self.status = status
        self.cell = cell
        self.ue_measurements = {}

    @property
    def plmnid(self):
        """Return the vbs."""

        return self.imsi.plmnid

    @property
    def vbs(self):
        """Return the vbs."""

        return self.cell.vbs

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = dict()
        out['imsi'] = self.imsi
        out['tmsi'] = self.tmsi
        out['rnti'] = self.rnti
        out['cell'] = self.cell
        out['plmnid'] = self.plmnid
        out['status'] = USER_STATUS[self.status]
        out['ue_measurements'] = self.ue_measurements
        return out

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "imsi=%s, tmsi=%u, rnti=%u" % (self.imsi, self.tmsi, self.rnti)

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.imsi)

    def __eq__(self, other):
        if isinstance(other, User):
            return self.imsi == other.imsi
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
