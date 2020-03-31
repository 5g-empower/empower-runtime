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
"""LNS Handlers for the LNS Discovery Server."""

import empower.managers.apimanager.apimanager as apimanager

from empower.core.eui64 import EUI64


class LGTWsHandler(apimanager.EmpowerAPIHandler):
    """REST API handler for managing LoRaWAN GTWs data (LNSD db)."""

    URLS = [
        r"/api/v1/lnsd/lnss/([a-zA-Z0-9:]*)/lgtws",
        r"/api/v1/lnsd/lnss/([a-zA-Z0-9:]*)/lgtws/([a-zA-Z0-9:]*)/?",
        ]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """List devices.

        Args:
            [0]: the lnss euid (optional)
            [1]: the lgtw euid (optional)

        Example URLs:
            GET /api/v1/lnsd/lnss/0000:0000:0000:0001/lgtws

            {
                "lns_euid": "0000000000000001",
                "lgtw_euid": [
                    "b827ebfffee77681"
                ]
            }

            GET /api/v1/lnsd/lnss/0000:0000:0000:0001/lgtws/b827:ebff:fee7:7681

            {
                "lns_euid": "0000000000000001",
                "lgtw_euid": "b827ebfffee77681"
            }
        """

        lns_euid = args[0]
        lgtw_euid = args[1] if len(args) == 2 else None

        out = []

        if lns_euid:
            lns_euid = EUI64(lns_euid)

        if lgtw_euid:
            lgtw_euid = EUI64(args[1])

        if not lns_euid and not lgtw_euid:
            # E.g. GET /api/v1/lnsd/lnss//lgtws/
            for key in self.service.lnss:
                out.append({"lns_euid": key,
                            "lgtw_euids": self.service.lnss[key].lgtws})

        elif (lns_euid in self.service.lnss and
              lgtw_euid in self.service.lnss[lns_euid].lgtws):
            # E.g. GET
            # /api/v1/lnsd/lnss/0000:0000:0000:0001/lgtws/b827:ebff:fee7:7681
            out = {"lns_euid": lns_euid,
                   "lgtw_euid": lgtw_euid}

        elif lns_euid in self.service.lnss and not lgtw_euid:
            # E.g.
            # GET /api/v1/lnsd/lnss/0000:0000:0000:0001/lgtws/
            out = {"lns_euid": lns_euid,
                   "lgtw_euid": self.service.lnss[lns_euid].lgtws}

        elif not lns_euid and lgtw_euid in self.service.lgtws:
            # E.g.
            # GET /api/v1/lnsd/lnss//lgtws/b827:ebff:fee7:7681
            for key in self.service.lgtws[lgtw_euid]:
                out.append({"lns_euid": key, "lgtw_euid": [lgtw_euid]})

        else:

            raise KeyError("Unable to find pair (%s, %s)" %
                           (lns_euid, lgtw_euid))

        return out

    @apimanager.validate(returncode=201, min_args=2, max_args=2)
    def post(self, *args, **kwargs):
        """Add a new LoRaWAN GTW to the LNS Discovery Server Database.

        Args:

            [0]: the lnss euid (mandatory)
            [1]: the lgtw euid (mandatory)

        Example URLs:

            POST /api/v1/lnsd/lnss/0000:0000:0000:0001/lgtws/
                b827:ebff:fee7:7681
        """

        lns_euid = EUI64(args[0])
        lgtw_euid = EUI64(args[1])

        self.service.add_lgtw(lns_euid=lns_euid, lgtw_euid=lgtw_euid)

        self.set_header("Location",
                        "/api/v1/lnsd/lnss/%s/lgtws/%s"
                        % (lns_euid, lgtw_euid))

    @apimanager.validate(returncode=204, min_args=1, max_args=2)
    def delete(self, *args, **kwargs):
        """Delete one or all LoRaWAN GTW from LSN Discovery Server.

        Args:

            [0]: the lnss euid
            [1]: the lgtw euid

        Example URLs:

            DELETE /api/v1/lnsd/lnss/0000:0000:0000:0001/lgtws
            DELETE /api/v1/lnsd/lnss/0000:0000:0000:0001/lgtws/
                b827:ebff:fee7:7681
        """
        lns_euid = None
        lgtw_euid = None

        if args[0]:
            lns_euid = EUI64(args[0])

        if len(args) == 2:
            if args[1]:
                lgtw_euid = EUI64(args[1])

        if len(args) == 2 and lns_euid and lgtw_euid:
            self.service.remove_lgtw(lgtw_euid, lns_euid)
        elif len(args) == 2 and not lns_euid and lgtw_euid:
            self.service.remove_lgtw(lgtw_euid)
        elif lns_euid:
            for lgtw_euid in self.service.lgtws:
                self.service.remove_lgtw(lgtw_euid, lns_euid)
        else:
            for lns_euid in self.service.lnss:
                for lgtw_euid in self.service.lgtws:
                    self.service.remove_lgtw(lgtw_euid, lns_euid)
