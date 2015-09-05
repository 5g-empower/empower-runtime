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

"""EmPOWER EtherAddress Class."""


class EtherAddress(object):
    """An Ethernet (MAC) address type."""

    def __init__(self, addr):
        """
        Understands Ethernet address is various forms. Hex strings, raw bytes
        strings, etc.
        """
        # Always stores as a 6 character string
        if isinstance(addr, bytes) or isinstance(addr, str):
            if len(addr) == 6:
                # raw
                pass
            elif len(addr) == 17 or len(addr) == 12 or addr.count(':') == 5:
                # hex
                if len(addr) == 17:
                    if addr[2::3] != ':::::' and addr[2::3] != '-----':
                        raise RuntimeError("Bad format for ethernet address")
                    # Address of form xx:xx:xx:xx:xx:xx
                    # Pick out the hex digits only
                    addr = ''.join(
                        (addr[x * 3:x * 3 + 2] for x in range(0, 6)))
                elif len(addr) == 12:
                    pass
                else:
                    # Assume it's hex digits but they may not all be in
                    # two-digit groupings (e.g., xx:x:x:xx:x:x). This actually
                    # comes up.
                    addr = ''.join(["%02x" % (int(x, 16),)
                                    for x in addr.split(":")])

                # We should now have 12 hex digits (xxxxxxxxxxxx).
                # Convert to 6 raw bytes.
                addr = b''.join(bytes((int(addr[x * 2:x * 2 + 2], 16),))
                                for x in range(0, 6))
            else:
                raise ValueError("Expected 6 raw bytes or some hex")
            self._value = addr
        elif isinstance(addr, EtherAddress):
            self._value = addr.to_raw()
        elif (type(addr) == list or
              (hasattr(addr, '__len__') and len(addr) == 6 and
               hasattr(addr, '__iter__'))):
            self._value = ''.join((chr(int(x, 16)) for x in addr))
        elif addr is None:
            self._value = '\x00' * 6
        else:
            raise ValueError("EtherAddress must be a string of 6 raw bytes")

    def is_global(self):
        """
        Returns True if this is a globally unique (OUI enforced) address.
        """
        return not self.is_local()

    def is_local(self):
        """
        Returns True if this is a locally-administered (non-global) address.
        """
        return True if (self._value[0] & 2) else False

    def is_multicast(self):
        """
        Returns True if this is a multicast address.
        """
        return True if (self._value[0] & 1) else False

    def to_raw(self):
        """
        Returns the address as a 6-long bytes object.
        """
        return self._value

    def to_tuple(self):
        """
        Returns a 6-entry long tuple where each entry is the numeric value
        of the corresponding byte of the address.
        """
        return tuple((x for x in self._value))

    def to_str(self, separator=':'):
        """
        Returns the address as string consisting of 12 hex chars separated
        by separator.
        """
        return separator.join(('%02x' % (x,) for x in self._value)).upper()

    def to_int(self, separator=':'):
        """
        Returns the address as string consisting of 12 hex chars separated
        by separator.
        """
        return int(self.to_str().replace(":", ""), 16)

    def match(self, other):
        """ Bitwise match. """
        if type(other) == EtherAddress:
            other = other.to_raw()
        elif type(other) == bytes:
            pass
        else:
            try:
                other = EtherAddress(other).to_raw()
            except RuntimeError:
                return False
        for cnt in range(0, 6):
            if (self._value[cnt] & other[cnt]) != self._value[cnt]:
                return False
        return True

    def __str__(self):
        return self.to_str()

    def __eq__(self, other):
        if type(other) == EtherAddress:
            other = other.to_raw()
        elif type(other) == bytes:
            pass
        else:
            try:
                other = EtherAddress(other).to_raw()
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

    @classmethod
    def bcast(cls):
        """ Return a broadcast address. """

        return EtherAddress('ff:ff:ff:ff:ff:ff')
