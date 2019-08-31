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

"""EmPOWER Virtual Access Point (VAP)."""

import logging


class VAP:
    """EmPOWER Virtual Access Point (VAP)

    Attributes:
        bssid: The VAP bssid address
        block: The resource block on which this VAP is scheduled
        ssid: The VAP ssid
    """

    def __init__(self, bssid, block, ssid):

        # read only parameters
        self.bssid = bssid
        self.block = block
        self.ssid = ssid

        # logger :)
        self.log = logging.getLogger(self.__class__.__module__)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        return {'bssid': self.bssid,
                'ssid': self.ssid,
                'block': self.block}

    @property
    def wtp(self):
        """Return the wtp on which this VAP is scheduled on."""

        if self.block:
            return self.block.wtp

        return None

    def clear_block(self):
        """Clear the block."""

        self.log.info("Deleting VAP: %s", self.bssid)

        self.block.wtp.connection.send_del_vap(self.bssid)

        self.block = None

    def to_str(self):
        """Return an ASCII representation of the object."""

        accum = []
        accum.append("bssid ")
        accum.append(str(self.bssid))
        accum.append(" ssid ")
        accum.append(str(self.ssid))
        accum.append(" block ")
        accum.append(str(self.block))

        return ''.join(accum)

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.bssid)

    def __eq__(self, other):
        if isinstance(other, VAP):
            return self.bssid == other.bssid
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
