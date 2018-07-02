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

"""EmPOWER DPID Class."""


class DPID:
    """An DPID type."""

    def __init__(self, addr):
        """
        Understands dpid in various forms. Hex strings, raw bytes
        strings, etc.
        """
        # Always stores as a 8 character string
        if isinstance(addr, bytes) and len(addr) == 8:
            # raw
            self._value = addr
        elif isinstance(addr, str):
            if len(addr) == 23 or addr.count(':') == 7:
                # hex
                if len(addr) == 23:
                    if addr[2::3] != ':::::::' and addr[2::3] != '-------':
                        raise RuntimeError("Bad format for dpid")
                    # dpid of form xx:xx:xx:xx:xx:xx:xx:xx
                    # Pick out the hex digits only
                    addr = ''.join(
                        (addr[x * 3:x * 3 + 2] for x in range(0, 8)))
                else:
                    # Assume it's hex digits but they may not all be in
                    # two-digit groupings (e.g., xx:x:x:xx:x:x:x:x).
                    # This actually comes up.
                    addr = ''.join(["%02x" % (int(x, 16),)
                                    for x in addr.split(":")])

                # We should now have 16 hex digits (xxxxxxxxxxxxxxxx).
                # Convert to 8 raw bytes.
                addr = b''.join(bytes((int(addr[x * 2:x * 2 + 2], 16),))
                                for x in range(0, 8))
            else:
                raise ValueError("Expected 8 raw bytes or some hex")
            self._value = addr
        elif isinstance(addr, DPID):
            self._value = addr.to_raw()
        elif addr is None:
            self._value = b'\x00' * 8
        else:
            raise ValueError("Dpid must be a string of 8 raw bytes")

    def to_raw(self):
        """
        Returns the dpid as a 8-long bytes object.
        """
        return self._value

    def to_tuple(self):
        """
        Returns a 8-entry long tuple where each entry is the numeric value
        of the corresponding byte of the dpid.
        """
        return tuple((x for x in self._value))

    def to_str(self, separator=':'):
        """
        Returns the dpid as string consisting of 16 hex chars separated
        by separator.
        """
        return separator.join(('%02x' % (x,) for x in self._value)).upper()

    def to_int(self, separator=':'):
        """
        Returns the dpid as string consisting of 16 hex chars separated
        by separator.
        """
        return int(self.to_str().replace(separator, ""), 16)

    def match(self, other):
        """ Bitwise match. """

        if isinstance(other, DPID):
            other = other.to_raw()
        elif isinstance(other, bytes):
            pass
        else:
            try:
                other = DPID(other).to_raw()
            except RuntimeError:
                return False
        for cnt in range(0, 8):
            if (self._value[cnt] & other[cnt]) != self._value[cnt]:
                return False
        return True

    def __str__(self):
        return self.to_str()

    def __eq__(self, other):

        if isinstance(other, DPID):
            other = other.to_raw()
        elif isinstance(other, bytes):
            pass
        else:
            try:
                other = DPID(other).to_raw()
            except RuntimeError:
                return False
        if self._value == other:
            return True
        return False

    def __hash__(self):
        return self._value.__hash__()

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"

    def __setattr__(self, a, v):
        if hasattr(self, '_value'):
            raise TypeError("This object is immutable")
        object.__setattr__(self, a, v)
