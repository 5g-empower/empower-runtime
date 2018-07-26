#!/usr/bin/env python3
#
# Copyright (c) 2018 Estefania Coronado
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

"""Incoming mcast address traffic module."""

import ipaddress

from datetime import datetime

from construct import UBInt8
from construct import UBInt32
from construct import Bytes
from construct import Struct

from empower.core.resourcepool import ResourceBlock
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import ModuleLVAPPEventWorker
from empower.core.module import ModuleTrigger

from empower.main import RUNTIME

PT_INCOMING_MCAST_ADDR = 0x46

INCOMING_MCAST_ADDR = Struct("incoming_mcast_address", UBInt8("version"),
                             UBInt8("type"),
                             UBInt32("length"),
                             UBInt32("seq"),
                             Bytes("wtp", 6),
                             Bytes("mcast_addr", 6),
                             Bytes("hwaddr", 6),
                             UBInt8("channel"),
                             UBInt8("band"))


class IncomingMcastAddress(ModuleTrigger):
    """ IGMPReport trigger object. """

    MODULE_NAME = "incoming_mcast_address"
    REQUIRED = ['module_type', 'worker', 'tenant_id']

    def __init__(self):
        super().__init__()

        # data structures
        self.mcast_addrs = {}

    def to_dict(self):
        """Return a JSON-serializable object."""

        out = super().to_dict()
        out['mcast_addrs'] = {str(k): v for k, v in self.mcast_addrs.items()}
        return out

    def handle_response(self, response):
        """ Handle an INCOM_MCAST_REQUEST event.
        Args:
            wtp, an WTP object
        Returns:
            None
        """

        wtp_addr = EtherAddress(response.wtp)

        if wtp_addr not in RUNTIME.wtps:
            return

        wtp = RUNTIME.wtps[wtp_addr]

        if wtp_addr not in RUNTIME.tenants[self.tenant_id].wtps:
            return

        hwaddr = EtherAddress(response.hwaddr)
        channel = response.channel
        band = response.band

        block = ResourceBlock(wtp, hwaddr, channel, band)
        self.mcast_addrs[EtherAddress(response.mcast_addr)] = block

        self.handle_callback(self)


class IncomingMcastAddressWorker(ModuleLVAPPEventWorker):
    """ Counter worker. """

    pass


def incoming_mcast_address(**kwargs):
    """Create a new module."""

    module = RUNTIME.components[IncomingMcastAddressWorker.__module__]
    return module.add_module(**kwargs)


def app_igmp_report(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return incoming_mcast_address(**kwargs)


setattr(EmpowerApp, IncomingMcastAddress.MODULE_NAME, app_igmp_report)


def launch():
    """Initialize the module."""

    return IncomingMcastAddressWorker(IncomingMcastAddress,
                                      PT_INCOMING_MCAST_ADDR,
                                      INCOMING_MCAST_ADDR)
