#!/usr/bin/env python3
#
# Copyright (c) 2018 Roberto Riggio
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

"""EmPOWER DSCP."""


class DSCP:
    """DSCP object representing a DSCP"""

    def __init__(self, dscp=0):

        if isinstance(dscp, str):
            self.dscp = int(dscp, 16)
        elif isinstance(dscp, int):
            self.dscp = dscp
        elif isinstance(dscp, DSCP):
            self.dscp = dscp.dscp
        else:
            raise ValueError("DSCP must be a string or a DSCP object")

    def to_raw(self):
        """ Return the bytes represenation of the DSCP """

        return self.dscp

    def to_str(self):
        """ Return the ASCII represenation of the DSCP """

        return "0x{:02x}".format(self.dscp).upper().replace("X", "x")

    def __bool__(self):
        return True if self.dscp else False

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.dscp)

    def __eq__(self, other):
        if isinstance(other, DSCP):
            return self.dscp == other.dscp
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
