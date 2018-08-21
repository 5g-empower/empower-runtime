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

"""EmPOWER Virtual Access Point (VAP) class."""


class VAP:
    """ The EmPOWER Virtual Access Point

    Attributes:
        bssid: The VAP bssid address.
        ssid: The VAP network name
        block: the resource blocks to which this LVAP is assigned.

    """

    def __init__(self, bssid, block, tenant):

        # read only params
        self.bssid = bssid
        self.block = block
        self.tenant = tenant

    @property
    def ssid(self):
        """ Get the SSID assigned to this LVAP. """

        return self.tenant.tenant_name

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the LVAP """

        return {'bssid': self.bssid,
                'ssid': self.ssid,
                'block': self.block}

    def __str__(self):

        accum = []
        accum.append("bssid ")
        accum.append(str(self.bssid))
        accum.append(" ssid ")
        accum.append(str(self.ssid))
        accum.append(" block ")
        accum.append(str(self.block))

        return ''.join(accum)

    def __hash__(self):
        return hash(self.bssid)

    def __eq__(self, other):
        if isinstance(other, VAP):
            return self.bssid == other.bssid
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
