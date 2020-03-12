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

    def add_lns(self, lns_euid, **kwargs):
        """Add a new LNS. Overwrites LNS if it already exists."""
        try:
            lns_euid = EUI64(lns_euid)
        except Exception as err:
            raise ValueError("LNS euid (lns_euid) not valid %s" % err)

        desc = kwargs.get("desc", "Generic LNS")
        uri = kwargs.get("uri")
        lgtws = kwargs.get("lgtws", [])

        # if lns_euid in self.lnss:
        #    raise ValueError(
        #        "LNS %s already registered in the LNS Discovery Server" %
        #        lns_euid)
        #    pass

        if lgtws:
            try:
                lgtws = [EUI64(lgtw).id6 for lgtw in lgtws]
                # TODO CHECK expression
            except Exception as err:
                raise ValueError("lGTW euids (%r) not valid - %s" %
                                 (lgtws, err))
            lns = LNS(uri=uri, euid=lns_euid, desc=desc, lgtws=lgtws).save()
        else:
            lns = LNS(uri=uri, euid=lns_euid, desc=desc).save()

        self.lnss[lns_euid] = lns

        return self.lnss[lns_euid]

    def update_lns(self, lns_euid, **kwargs):
        """Update lns data."""
        lns_euid = EUI64(lns_euid)
        desc = kwargs.get("desc")
        uri = kwargs.get("uri")
        lgtws = kwargs.get("lgtws", [])

        try:
            lns = self.lnss[lns_euid]
        except KeyError:
            raise KeyError("%s not registered, register lns first" % lns_euid)

        if lgtws:
            try:
                lgtws = [EUI64(lgtw) for lgtw in lgtws]
            except Exception as err:
                raise ValueError("lGTW euids (%r) not valid - %s" %
                                 (lgtws, err))
            for lgtw in lgtws:
                if lgtw not in lns.lgtws:
                    lns.lgtws.append(lgtw)

        if uri:
            lns.uri = uri

        if desc:
            lns.desc = desc

        lns.save()

    def remove_lns(self, lns_euid):
        """Remove LNS."""
        try:
            lns_euid = EUI64(lns_euid)
        except Exception:
            raise ValueError("LNS euid (lns_euid) not valid")
        if lns_euid not in self.lnss:
            raise ValueError("%s not registered" % lns_euid)
        lns = self.lnss[lns_euid]
        lns.delete()
        del self.lnss[lns_euid]

    def remove_all_lnss(self):
        """Remove all LNSs."""
        for lns_euid in list(self.lnss):
            lns = self.lnss[lns_euid]
            lns.delete()
            del self.lnss[lns_euid]

    def add_lgtw(self, **kwargs):
        """Add new lgtw."""
        if 'lns_euid' not in kwargs:
            raise ValueError("lns_euid must be present")
        if 'lgtw_euid' not in kwargs:
            raise ValueError("lgtw_euid must be present")

        lns_euid = EUI64(kwargs.get("lns_euid"))
        lgtw_euid = EUI64(kwargs.get("lgtw_euid"))
        try:
            lns = self.lnss[lns_euid]
        except KeyError:
            raise KeyError("%s not registered, register lns first" % lns_euid)

        if lgtw_euid not in lns.lgtws:
            if lns.lgtws:
                lns.lgtws.append(lgtw_euid)
            else:
                lns.lgtws = [lgtw_euid]
            lns.save()
            self.lnss[lgtw_euid] = lns

        return lgtw_euid

    def remove_lgtw_from_lns(self, lgtw_euid, lns_euid):
        """Remove GTW from an LNS."""
        try:
            lns = self.lnss[lns_euid]
        except KeyError:
            raise ValueError("%s not registered" % lns_euid)

        if lgtw_euid in lns.lgtws:
            print(lgtw_euid)
            lns.lgtws.remove(lgtw_euid)
            lns.save()
            self.lnss[lns_euid] = lns

    def remove_lgtw(self, lgtw_euid, lns_euid=None):
        """Remove GTW (is an LNS is not specified, remove for all)."""
        if lns_euid:
            self.remove_lgtw_from_lns(lgtw_euid, lns_euid)
        else:
            for item_euid in self.lnss:
                self.remove_lgtw_from_lns(lgtw_euid, item_euid)


def launch(context, service_id, port=DEFAULT_PORT):
    """Initialize the module."""
    return LNSDPManager(context=context, service_id=service_id, port=port)
