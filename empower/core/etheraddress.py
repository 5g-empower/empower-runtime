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

"""Ethernet address."""

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField


class EtherAddress:
    """Ethernet address."""

    def __init__(self, addr=None):

        if not addr:
            addr = "00:00:00:00:00:00"

        # Always stores as a 6 character string
        if isinstance(addr, bytes) and len(addr) == 6:
            # raw
            self._value = addr
        elif isinstance(addr, str):
            if len(addr) == 17 or addr.count(':') == 5:
                # hex
                if len(addr) == 17:
                    if addr[2::3] != ':::::' and addr[2::3] != '-----':
                        raise RuntimeError("Bad format for ethernet address")
                    # Address of form xx:xx:xx:xx:xx:xx
                    # Pick out the hex digits only
                    addr = ''.join(
                        (addr[x * 3:x * 3 + 2] for x in range(0, 6)))
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
        elif addr is None:
            self._value = b'\x00' * 6
        else:
            raise ValueError("EtherAddress must be a string of 6 raw bytes")

    def is_global(self):
        """Returns True if this is a globally unique (OUI enforced) address."""
        return not self.is_local()

    def is_local(self):
        """Returns True if this is a locally-administered address."""
        return bool(self._value[0] & 2)

    def is_multicast(self):
        """Returns True if this is a multicast address."""

        return bool(self._value[0] & 1)

    def to_raw(self):
        """Returns the address as a 6-long bytes object."""

        return self._value

    def to_str(self, separator=':'):
        """Return an ASCII representation of the object."""

        return separator.join(('%02x' % (x,) for x in self._value)).upper()

    def match(self, other):
        """ Bitwise match. """

        if isinstance(other, EtherAddress):
            other = other.to_raw()
        elif isinstance(other, bytes):
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

        if isinstance(other, EtherAddress):
            other = other.to_raw()
        elif isinstance(other, bytes):
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


class EtherAddressField(MongoBaseField):
    """A field that stores EtherAddresses."""

    def __init__(self, verbose_name=None, mongo_name=None, **kwargs):

        super(EtherAddressField, self).__init__(verbose_name=verbose_name,
                                                mongo_name=mongo_name,
                                                **kwargs)

        def validate_ethernet_address(value):

            try:
                EtherAddress(value)
            except ValueError:
                msg = '%r is not a valid Ethernet address.' % value
                raise ValidationError(msg)

        self.validators.append(validate_ethernet_address)

    @classmethod
    def to_mongo(cls, value):
        """Convert value for storage."""

        try:
            return str(value)
        except ValueError:
            msg = '%r is not a valid Ethernet address.' % value
            raise ValidationError(msg)

    @classmethod
    def to_python(cls, value):
        """Convert value back to Python."""

        try:
            return EtherAddress(value)
        except ValueError:
            msg = '%r is not a valid Ethernet address.' % value
            raise ValidationError(msg)
