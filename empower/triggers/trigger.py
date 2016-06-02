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

"""Trigger module."""

from empower.core.module import Module
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.datatypes.etheraddress import EtherAddress

from empower.main import RUNTIME


class Trigger(Module):
    """ RSSI trigger object. """

    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    def __init__(self):
        Module.__init__(self)
        self._addrs = EtherAddress('FF:FF:FF:FF:FF:FF')
        self._block = None

    def run_once(self):
        """ Send out trigger configuration. """

        pass

    @property
    def addrs(self):
        """ Return the address. """
        return self._addrs

    @addrs.setter
    def addrs(self, addr):
        """ Set the address. """
        self._addrs = EtherAddress(addr)

    @property
    def block(self):
        """Return block."""

        return self._block

    @block.setter
    def block(self, value):
        """Set block."""

        if isinstance(value, ResourceBlock):

            self._block = value

        elif isinstance(value, dict):

            wtp = RUNTIME.wtps[EtherAddress(value['wtp'])]

            if 'hwaddr' not in value:
                raise ValueError("Missing field: hwaddr")

            if 'channel' not in value:
                raise ValueError("Missing field: channel")

            if 'band' not in value:
                raise ValueError("Missing field: band")

            if 'wtp' not in value:
                raise ValueError("Missing field: wtp")

            incoming = ResourcePool()
            block = ResourceBlock(wtp, EtherAddress(value['hwaddr']),
                                  int(value['channel']), int(value['band']))
            incoming.add(block)

            match = wtp.supports & incoming

            if not match:
                raise ValueError("No block specified")

            if len(match) > 1:
                raise ValueError("More than one block specified")

            self._block = match.pop()

    def handle_response(self, message):
        """Handle a TRIGGER message."""

        pass

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Trigger """

        out = super().to_dict()

        out['addrs'] = self.addrs
        out['block'] = self.block

        return out

    def __eq__(self, other):

        return super().__eq__(other) and self.addrs == other.addrs and \
            self.block == other.block
