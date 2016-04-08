#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""EmPOWER SSID."""

import re


class SSID(object):
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
