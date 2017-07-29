#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

"""EmPOWER EtherAddress Class."""


class PLMNID(object):
    """An Ethernet (MAC) address type."""

    def __init__(self, plmn_id=None):
        """Understands PLMNID in int and string form."""

        if isinstance(plmn_id, str):
            if len(plmn_id) == 5 or len(plmn_id) == 6:
                tokens = [int(x) for x in list(plmn_id)]
                self._value = "".join([str(x) for x in tokens])
            else:
                raise ValueError("Expected 5/6 integers")

        elif isinstance(plmn_id, int):
            self._value = PLMNID(str(plmn_id)).to_str()

        elif isinstance(addr, PLMNID):
            self._value = addr.to_str()

        elif addr is None:
            self._value = "00000"

        else:
            raise ValueError("Expected 5/6 integers")

    def to_tuple(self):
        """Return the plmnid as a mcc/mnc tuple."""

        tokens = list(self._value)
        return ("".join(tokens[0:3]), "".join(tokens[3:]))

    def to_str(self):
        """Return the plmnid as a string."""

        return self._value

    @property
    def mcc(self):
        """Return the mcc."""

        return self.to_tuple()[0]

    @property
    def mnc(self):
        """Return the mnc."""

        return self.to_tuple()[1]

    def __str__(self):
        return self.to_str()

    def __eq__(self, other):

        if type(other) != PLMNID:
            return false

        return self.to_str() == other.to_str()

    def __hash__(self):
        return self._value.__hash__()

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
