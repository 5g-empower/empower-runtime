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

"""EmPOWER Match."""


def conflicting_match(matches, new_match):

    for match in matches:

        common = {cond: value for cond, value in new_match.match.items()
                  if cond in match.match and value == match.match[cond]}

        if common == new_match.match or common == match.match:
            return match

    return None


class Match:
    """Match object representing an OpenFlow match rules"""

    def __init__(self, match):

        if isinstance(match, Match):
            pass
        elif isinstance(match, dict):
            self.match = self.__ofmatch_s2d(self.__ofmatch_d2s(match))
        elif isinstance(match, str):
            self.match = self.__ofmatch_s2d(match.replace(" ", ""))
        else:
            raise ValueError("Match must be string, dict, or Match")

    @classmethod
    def __ofmatch_d2s(cls, match):
        """Convert an OFMatch from dictionary to string."""

        matches = []

        for tmp in sorted(match.items()):

            if tmp[0] == 'dl_vlan':
                value = "%s=%u" % tmp
            elif tmp[0] == 'dl_type':
                value = "%s=%s" % (tmp[0], "0x{:04x}".format(tmp[1]))
            elif tmp[0] == 'in_port':
                value = "%s=%u" % tmp
            elif tmp[0] == 'nw_proto':
                value = "%s=%u" % tmp
            elif tmp[0] == 'tp_dst':
                value = "%s=%u" % tmp
            elif tmp[0] == 'tp_src':
                value = "%s=%u" % tmp
            else:
                value = "%s=%s" % tmp

            matches.append(value)

        return ",".join(matches)

    @classmethod
    def __ofmatch_s2d(cls, match):
        """Convert an OFMatch from string to dictionary."""

        key = {}

        if match == "":
            return key

        for token in match.lower().split(","):

            key_t, value_t = token.split("=")

            if key_t == 'dl_vlan':
                value_t = int(value_t)

            if key_t == 'dl_type':
                value_t = int(value_t, 16)

            if key_t == 'in_port':
                value_t = int(value_t)

            if key_t == 'nw_proto':
                value_t = int(value_t)

            if key_t == 'tp_dst':
                value_t = int(value_t)

            if key_t == 'tp_src':
                value_t = int(value_t)

            key[key_t] = value_t

        return key

    def to_str(self):
        """ Return the ASCII representation of the OFMatch """

        return self.__ofmatch_d2s(self.match)

    def __bool__(self):
        return True if self.match else False

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.to_str())

    def __eq__(self, other):
        if isinstance(other, Match):
            return self.match == other.match
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
