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

"""Common channel quality and conflict maps module."""

from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import SBInt8
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import Array

from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import Module
from empower.core.resourcepool import CQM
from empower.core.resourcepool import ResourceBlock
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME

PT_BUSYNESS_REQUEST = 0x36
PT_BUSYNESS_RESPONSE = 0x37

BUSYNESS_REQUEST = Struct("busyness_request", UBInt8("version"),
                          UBInt8("type"),
                          UBInt32("length"),
                          UBInt32("seq"),
                          UBInt32("module_id"),
                          Bytes("hwaddr", 6),
                          UBInt8("channel"),
                          UBInt8("band"))

BUSYNESS_RESPONSE = Struct("busyness_response", UBInt8("version"),
                           UBInt8("type"),
                           UBInt32("length"),
                           UBInt32("seq"),
                           UBInt32("module_id"),
                           Bytes("wtp", 6),
                           UBInt32("busyness"))


class Busyness(Module):
    """ A maps poller. """

    MODULE_NAME = "busyness"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._block = None

        # data structures
        self.busyness = None

    def __eq__(self, other):
        return super().__eq__(other) and self.block == other.block

    @property
    def block(self):
        return self._block

    @block.setter
    def block(self, value):

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

            # Check if block is valid
            incoming = ResourceBlock(wtp, EtherAddress(value['hwaddr']),
                                     int(value['channel']),
                                     int(value['band']))

            match = [block for block in wtp.supports if block == incoming]

            if not match:
                raise ValueError("No block specified")

            if len(match) > 1:
                raise ValueError("More than one block specified")

            self._block = match[0]

    def to_dict(self):
        """ Return a JSON-serializable dictionary. """

        out = super().to_dict()
        out['block'] = self.block.to_dict()
        out['busyness'] = self.busyness

        return out

    def run_once(self):
        """ Send out request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]
        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            self.log.info("WTP %s not found", wtp.addr)
            self.unload()
            return

        if not wtp.connection or wtp.connection.stream.closed():
            self.log.info("WTP %s not connected", wtp.addr)
            self.unload()
            return

        req = Container(version=PT_VERSION,
                        type=PT_BUSYNESS_REQUEST,
                        length=22,
                        seq=wtp.seq,
                        module_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        hwaddr=self.block.hwaddr.to_raw(),
                        channel=self.block.channel,
                        band=self.block.band)

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, self.block, self.module_id)

        msg = BUSYNESS_REQUEST.build(req)
        wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming poller response message.
        Args:
            message, a poller response message
        Returns:
            None
        """

        self.busyness = response.busyness / 180.0
        self.block.busyness = response.busyness / 180.0

        # call callback
        self.handle_callback(self)


class BusynessWorker(ModuleLVAPPWorker):
    """ Counter worker. """

    pass


def busyness(**kwargs):
    """Create a new module."""

    return RUNTIME.components[BusynessWorker.__module__].add_module(**kwargs)


def bound_busyness(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return busyness(**kwargs)

setattr(EmpowerApp, Busyness.MODULE_NAME, bound_busyness)


def launch():
    """ Initialize the module. """

    return BusynessWorker(Busyness, PT_BUSYNESS_RESPONSE, BUSYNESS_RESPONSE)
