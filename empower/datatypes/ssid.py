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

"""EmPOWER SSID."""

import re


class SSID:
    """SSID object representing an alphanumeric SSID

    Attributes:
        ssid: The SSID's alphanumeric identifier. Only alphanumeric characters
              are accepted (a - z, A - Z, 0 - 9)
    """

    def __init__(self, ssid):

        if isinstance(ssid, bytes):
            self.ssid = ssid.decode('UTF-8')
        elif isinstance(ssid, str):
            allowed = re.compile(r'^[a-zA-Z0-9_]+$',
                                 re.VERBOSE | re.IGNORECASE)
            if allowed.match(ssid) is None:
                raise ValueError("Invalid SSID name")
            self.ssid = ssid
        elif isinstance(ssid, SSID):
            self.ssid = str(ssid)
        else:
            raise ValueError("SSID must be a string or an array of UTF-8 "
                             "encoded bytes array of UTF-8 encoded bytes")

    def to_raw(self):
        """ Return the bytes represenation of the SSID """
        return self.ssid.encode('UTF-8')

    def to_str(self):
        """ Return the ASCII represenation of the SSID """
        return self.ssid

    def __bool__(self):
        return True if self.ssid else False

    def __str__(self):
        return self.to_str()

    def __len__(self):
        return len(self.ssid)

    def __hash__(self):
        return hash(self.ssid)

    def __eq__(self, other):
        if isinstance(other, SSID):
            return self.ssid == other.ssid
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
