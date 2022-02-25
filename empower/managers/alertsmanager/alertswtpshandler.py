#!/usr/bin/env python3
#
# Copyright (c) 2022 Roberto Riggio
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

"""Exposes a RESTful interface ."""

import uuid

import empower_core.apimanager.apimanager as apimanager

from empower_core.etheraddress import EtherAddress


# pylint: disable=W0223
class AlertsWTPsHandler(apimanager.APIHandler):
    """WTPs handler"""

    URLS = [r"/api/v1/alerts/([a-zA-Z0-9-]*)/wtps/?",
            r"/api/v1/alerts/([a-zA-Z0-9-]*)/wtps/([a-zA-Z0-9:]*)/?"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, *args, **kwargs):
        """Lists all the WTP.

        Args:

            [0], the alert id (mandatory)
            [1], the wtp id (optional)

        Example URLs:

            GET /api/v1/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps
            GET /api/v1/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/wtps/
                00:0D:B9:54:27:F8
        """

        alert_id = uuid.UUID(args[0])
        alerts = self.service.alerts[alert_id]

        if len(args) == 1:
            return alerts

        if EtherAddress(args[1]) in alerts.get_wtps():
            return EtherAddress(args[1])

        raise KeyError()

    @apimanager.validate(returncode=201, min_args=2, max_args=2)
    def post(self, *args, **kwargs):
        """Add a WTP.

        Args:

            [0], the alert id (mandatory)
            [1], the wtp id
        """

        alert_id = uuid.UUID(args[0])
        wtp = EtherAddress(args[1])

        self.service.add_wtp(alert_id=alert_id, wtp=wtp)

        self.set_header("Location",
                        "/api/v1/alerts/%s/wtps/%s" % (alert_id, wtp))

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def delete(self, *args, **kwargs):
        """Delete one wtp.

        Args:

            [0], the alert id
            [1], the wtp id

        Example URLs:

            DELETE /api/v1/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26/subs/
                00:0D:B9:2F:56:64
        """

        alert_id = uuid.UUID(args[0])
        wtp = EtherAddress(args[1])

        self.service.del_wtp(alert_id=alert_id, wtp=wtp)
