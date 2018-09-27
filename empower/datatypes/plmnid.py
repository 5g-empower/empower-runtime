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

"""EmPOWER PLMNID."""

import re


class PLMNID:
    """PLMNID object representing a PLMNID

    Attributes:
        plmnid: The PLMNID. Only numeric characters are accepted (0 - 9)
    """

    def __init__(self, plmnid=bytes(16)):

        if isinstance(plmnid, str):
            allowed = re.compile(r'^[f0-9]+$', re.VERBOSE | re.IGNORECASE)
            if allowed.match(plmnid) is None:
                raise ValueError("Invalid PLMNID name")
            self.plmnid = plmnid.lower()
        elif isinstance(plmnid, bytes):
            self.plmnid = plmnid[1:].hex()
        elif isinstance(plmnid, PLMNID):
            self.plmnid = str(plmnid)
        else:
            raise ValueError("PLMNID must be a string")

    def to_raw(self):
        """ Return the bytes represenation of the PLMNID """
        return int(self.plmnid, 16).to_bytes(4, byteorder='big')

    def to_str(self):
        """ Return the ASCII represenation of the PLMNID """
        return self.plmnid

    def __bool__(self):
        return True if self.plmnid else False

    def __str__(self):
        return self.to_str()

    def __len__(self):
        return len(self.plmnid)

    def __hash__(self):
        return hash(self.plmnid)

    def __eq__(self, other):
        if isinstance(other, PLMNID):
            return self.plmnid == other.plmnid
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
