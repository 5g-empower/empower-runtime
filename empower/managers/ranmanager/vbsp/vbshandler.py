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

"""VBSP Handlers."""

import empower.managers.apimanager.apimanager as apimanager

from empower.core.etheraddress import EtherAddress


# pylint: disable=W0223
class VBSHandler(apimanager.EmpowerAPIHandler):
    """Handler for accessing VBSes."""

    URLS = [r"/api/v1/vbses/?",
            r"/api/v1/vbses/([a-zA-Z0-9:]*)/?"]

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List devices.

        Args:

            [0]: the device address (optional)

        Example URLs:

            GET /api/v1/vbses

            [
                {
                    "addr": "00:00:00:00:00:01",
                    "cells": {},
                    "connection": null,
                    "desc": "Ettus B210",
                    "last_seen": 0,
                    "last_seen_ts": "1970-01-01T01:00:00.000000Z",
                    "period": 0,
                    "state": "disconnected"
                }
            ]

            GET /api/v1/vbses/00:00:00:00:00:01

            {
                "addr": "00:00:00:00:00:01",
                "cells": {},
                "connection": null,
                "desc": "Ettus B210",
                "last_seen": 0,
                "last_seen_ts": "1970-01-01T01:00:00.000000Z",
                "period": 0,
                "state": "disconnected"
            }
        """

        return self.service.devices \
            if not args else self.service.devices[EtherAddress(args[0])]

    @apimanager.validate(returncode=201, min_args=0, max_args=0)
    def post(self, *args, **kwargs):
        """Add a new device.

        Request:

            version: protocol version (1.0)
            addr: the device address (mandatory)
            desc: a human readable description of the device (optional)

        Example URLs:

            POST /api/v1/vbses

            {
                "version":"1.0",
                "addr": "00:00:00:00:00:01"
            }

            POST /api/v1/vbses

            {
                "version":"1.0",
                "addr": "00:00:00:00:00:01",
                "desc": "Ettus B210"
            }
        """

        device = self.service.create(**kwargs)

        self.set_header("Location", "/api/v1/vbses/%s" % device.addr)

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all devices.

        Args:

            [0]: the device address

        Example URLs:

            DELETE /api/v1/vbses
            DELETE /api/v1/vbses/00:00:00:00:00:01
        """

        if args:
            self.service.remove(EtherAddress(args[0]))
        else:
            self.service.remove_all()
