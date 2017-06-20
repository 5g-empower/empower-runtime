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

"""CQM links module."""

import time

from construct import UBInt8
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import UBInt16
from construct import UBInt32
from construct import Array

from empower.lvapp import PT_VERSION
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import LVAPPServer
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.module import Module
from empower.core.app import EmpowerApp

from empower.main import RUNTIME


PT_CQM_LINKS_REQUEST = 0x43
PT_CQM_LINKS_RESPONSE = 0x44

CQM_LINK = Sequence("stats",
                    Bytes("ta", 6),
                    UBInt32("p_channel_busy_fraction"),
                    UBInt32("p_throughput"),
                    UBInt32("p_available_bw"),
                    UBInt32("p_pdf"),
                    UBInt32("p_attainable_throughput"))

CQM_LINKS_REQUEST = Struct("stats_request", UBInt8("version"),
                           UBInt8("type"),
                           UBInt32("length"),
                           UBInt32("seq"),
                           UBInt32("module_id"))

CQM_LINKS_RESPONSE = \
    Struct("stats_response", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("wtp", 6),
           UBInt16("nb_links"),
           Array(lambda ctx: ctx.nb_links, CQM_LINK))


class CQMLinks(Module):
    """ CQM_links object.

    This primitive retrieves the Channel quality map links from a WTP

    For example:

        cqm_links(wtp="11:22:33:44:55:66",
                  every=2000,
                  callback=cqm_links_callback)
    """

    MODULE_NAME = "cqm_links"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'wtp']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self._wtp = None

        # data structures
        self.cqm_links = {}

    def __eq__(self, other):

        return super().__eq__(other) and self.wtp == other.wtp

    @property
    def wtp(self):
        """Return the WTP Address."""

        return self._wtp

    @wtp.setter
    def wtp(self, value):
        """Set the WTP Address."""

        self._wtp = EtherAddress(value)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Stats """

        out = super().to_dict()

        out['wtp'] = self.wtp
        out['cqm_links'] = {str(k): v for k, v in self.cqm_links.items()}

        return out

    def run_once(self):
        """ Send out stats request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.wtp not in tenant.wtps:
            self.log.info("WTP %s not found", self.wtp)
            self.unload()
            return

        wtp = tenant.wtps[self.wtp]

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        if not wtp.connection or wtp.connection.stream.closed():
            self.log.info("WTP %s not connected", wtp.addr)
            self.unload()
            return

        stats_req = Container(version=PT_VERSION,
                              type=PT_CQM_LINKS_REQUEST,
                              length=14,
                              seq=wtp.seq,
                              module_id=self.module_id)

        msg = CQM_LINKS_REQUEST.build(stats_req)
        wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming STATS_RESPONSE message.
        Args:
            stats, a STATS_RESPONSE message
        Returns:
            None
        """

        # update this object
        self.cqm_links = {}

        for entry in response.stats:

            addr = EtherAddress(entry[0])

            if addr not in RUNTIME.lvaps:
                continue

            lvap = RUNTIME.lvaps[addr]

            if not lvap.tenant or lvap.tenant.tenant_id != self.tenant_id:
                continue

            value = {'addr': addr,
                     'p_channel_busy_fraction': entry[1] / 180.0,
                     'p_throughput': entry[2] / 180.0,
                     'p_available_bw': entry[3] / 180.0,
                     'p_pdr': entry[4] / 180.0,
                     'p_attainable_throughput': entry[5] / 180.0
                     }

            self.cqm_links[addr] = value

        # call callback
        self.handle_callback(self)


class CQMLinksWorker(ModuleLVAPPWorker):
    """Counter worker."""

    pass


def cqm_links(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[CQMLinksWorker.__module__]
    return worker.add_module(**kwargs)


def bound_cqm_links(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return cqm_links(**kwargs)

setattr(EmpowerApp, CQMLinks.MODULE_NAME, bound_cqm_links)


def launch():
    """ Initialize the module. """

    return CQMLinksWorker(CQMLinks, PT_CQM_LINKS_RESPONSE, CQM_LINKS_RESPONSE)
