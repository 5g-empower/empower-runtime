#!/usr/bin/env python3
#
# Copyright (c) 2020 Fondazione Bruno Kessler
# Author(s): Cristina Costa (ccosta@fbk.eu)
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

"""LoRaWAN NS Discovery WS Server Manager."""

from empower.managers.lommmanager.wsmanager import WSManager
from empower.managers.lommmanager.lnsdp.lnsshandler import LNSsHandler
from empower.managers.lommmanager.lnsdp.lgtwshandler import LGTWsHandler
from empower.managers.lommmanager.lnsdp.lnsdpmainhandler \
    import LNSDPMainHandler
from empower.managers.lommmanager.lnsdp.lns import LNS
from empower.core.eui64 import EUI64

DEFAULT_PORT = 6038


class LNSDPManager(WSManager):
    """LNS Discovery Server Manager.

    Parameters:
        port: the port on which the WS server should listen (optional,
            default: 6038)
    """

    HANDLERS = [LNSsHandler, LGTWsHandler]
    WSHANDLERS = [LNSDPMainHandler]

    def __init__(self, context, service_id, port):
        """Initilize arguments."""
        super().__init__(context=context, service_id=service_id, port=port)
        self.lnss = {}

    @property
    def lgtws(self):
        """Return the lgtws."""
        lgtws = {}
        for lns_euid in self.lnss:
            lns = self.lnss[lns_euid]
            for lgtw_euid in lns.lgtws:
                if lgtw_euid not in lgtws:
                    lgtws[lgtw_euid] = []
                lgtws[lgtw_euid].append(lns_euid)
        return lgtws

    def start(self):
        """Start control loop."""
        super().start()

        # retrieve LNS data from the db
        for lns in LNS.objects:
            self.lnss[lns.euid] = lns

    def add_lns(self, euid, uri, lgtws=None, desc="Generic LNS"):
        """Add a new LNS."""

        if euid in self.lnss:
            raise ValueError("LNS %s already defined" % euid)

        if not lgtws:
            lgtws = []
        else:
            lgtws = [EUI64(lgtw).id6 for lgtw in lgtws]

        lns = LNS(uri=uri, euid=euid, desc=desc, lgtws=lgtws).save()

        self.lnss[euid] = lns

        return self.lnss[euid]

    def update_lns(self, euid, uri, lgtws=None, desc="Generic LNS"):
        """Update LNS data."""

        lns = self.lnss[euid]

        if not lgtws:
            lgtws = []
        else:
            lgtws = [EUI64(lgtw).id6 for lgtw in lgtws]

        try:
            lns.uri = uri
            lns.desc = desc
            lns.lgtws = lgtws
            lns.save()
        finally:
            lns.refresh_from_db()

        return self.lnss[euid]

    def remove_lns(self, euid):
        """Remove LNS."""

        lns = self.lnss[euid]
        lns.delete()
        del self.lnss[euid]

    def remove_all_lnss(self):
        """Remove all LNSs."""

        for euid in list(self.lnss):
            self.remove_lns(euid)

    def add_lgtw(self, lns_euid, lgtw_euid):
        """Add LGTW to an LNS."""

        lns = self.lnss[lns_euid]

        try:
            if lgtw_euid not in lns.lgtws:
                lns.lgtws.append(lgtw_euid)
            lns.save()
        finally:
            lns.refresh_from_db()

    def remove_lgtw_from_lns(self, lgtw_euid, lns_euid):
        """Remove LGTW from an LNS."""

        lns = self.lnss[lns_euid]

        try:
            if lgtw_euid in lns.lgtws:
                lns.lgtws.remove(lgtw_euid)
            lns.save()
        finally:
            lns.refresh_from_db()

    def remove_lgtw(self, lgtw_euid, lns_euid=None):
        """Remove LGTW (if an LNS is not specified, remove for all)."""

        if lns_euid:
            self.remove_lgtw_from_lns(lgtw_euid, lns_euid)
        else:
            for item_euid in self.lnss:
                self.remove_lgtw_from_lns(lgtw_euid, item_euid)


def launch(context, service_id, port=DEFAULT_PORT):
    """Initialize the module."""

    return LNSDPManager(context=context, service_id=service_id, port=port)
