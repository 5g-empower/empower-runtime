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

# TODO ADD REFERENCE TO ALLOWED DEVICES

"""LNS Handlers for the LNS Discovery Server."""

import json, traceback

import empower.managers.apimanager.apimanager as apimanager

from empower.core.eui64 import EUI64

class LNSsHandler(apimanager.EmpowerAPIHandler):
    """Handler for accessing LNS."""

    URLS = [r"/api/v1/lnsd/lnss/?",
            r"/api/v1/lnsd/lnss/([a-zA-Z0-9:]*)/?"] # TODO CHECK EUI64 FORMAT

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List devices.

        Args:

            [0]: the lns euid (optional)

        Example URLs:

            GET /api/v1/lnsd/lnss

            [
                {
                "euid":"::1",
                "uri":"ws://0.0.0.0:6038/router-",
                "desc": "LNS XXX"
                }
            ]

            GET /api/v1/lnsd/lnss/::1

            {
            "euid":"::1",
            "uri":"ws://0.0.0.0:6038/router-",
            "desc": "LNS XXX"
            }



        """
        if not args:
            out = []
            desc      = self.get_argument("desc",None)
            state     = self.get_argument("state",None)
            lgtw_euid = self.get_argument("lgtw_euid",None)
            for key in self.service.lnss:
                """ only if string in description """
                if desc and desc not in self.service.lnss[key].to_dict()["desc"]:
                    continue
                """ only if state matches """
                if state and state != self.service.lnss[key].to_dict()["state"]:
                    continue
                """ only if manages lgtw_id """
                if lgtw_euid and lgtw_euid not in self.service.lnss[key].to_dict()["lgtws"]:
                    continue
                """ all """
                out.append(self.service.lnss[key].to_dict())
            return out
        else:
            try:
                lnss = self.service.lnss[EUI64(args[0]).id6].to_dict()
            except KeyError as err:
                self.set_status(400)
                self.finish({"status_code":400,"title":"LNS not found","detail":str(err)})
            else:
                return lnss

    @apimanager.validate(returncode=201, min_args=1, max_args=1)
    def post(self, *args, **kwargs):
        """Add a new LNS to the LNS Discovery Server Database.

        Request:

            version: protocol version (1.0)
            euid: the lns id in eui64 or id6 format (mandatory)
            uri: the lns uri template (mandatory)
            desc: a human readable description of the device (optional)

        Example URLs:

            POST /api/v1/lnsd/lnss/"::1"

            {
                "version":"1.0",
                "lgtws":["b827:ebff:fee7:7681"],
                "uri":"ws://0.0.0.0:6038/router-",
                "desc": "LNS XXX"
            }
        """
        try:
            lnss = self.service.add_lns(args[0], **kwargs)
        except ValueError as err:
            self.set_status(400)
            self.finish({"status_code":400,"title":"Value error","detail":str(err)})
        else:
            self.set_header("Location", "/api/v1/lnsd/lnss/%s" % lnss.euid)


    @apimanager.validate(returncode=201, min_args=1, max_args=1)
    def put(self, *args, **kwargs):
        """Add a new LNS to the LNS Discovery Server Database.

        Args:

            [0]: the lns euid (mandatory)

        Request:

            version: protocol version (1.0)
            uri: the lns uri template (mandatory)
            desc: a human readable description of the device (optional)

        Example URLs:

            PUT /api/v1/lnsd/lnss/::1

            {
                "version":"1.0",
                "lgtws":["b827:ebff:fee7:7681"],
                "uri":"ws://0.0.0.0:6038/router-",
                "desc": "LNS XXX"
            }
        """
        try:
            self.service.update_lns(args[0], **kwargs)
        except ValueError as err:
            self.set_status(400)
            self.finish({"status_code":400,"title":"Value error","detail":str(err)})
        else:
            self.set_header("Location", "/api/v1/lnsd/lnss/%s" % args[0])

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all devices.

        Args:

            [0]: the lnss euid

        Example URLs:

            DELETE /api/v1/lnsd/lnss
            DELETE /api/v1/lnsd/lnss/00-0D-B9-2F-56-64
        """

        if args:
            try:
                self.service.remove_lns(EUI64(args[0]).id6)
            except ValueError as err:
                self.set_status(400)
                self.finish({"status_code":400,"title":"Value error",
                            "detail":str(err)})
            except:
                self.set_status(500)
                self.finish({"status_code":500,"title":"Server error",
                            "detail":"unknown internal error"})
        else:
            self.service.remove_all_lnss()
