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


# pylint: disable=W0223
class AlertsHandler(apimanager.APIHandler):
    """Alerts handler"""

    URLS = [r"/api/v1/alerts/?",
            r"/api/v1/alerts/([a-zA-Z0-9-]*)/?"]

    @apimanager.validate(min_args=0, max_args=1)
    def get(self, *args, **kwargs):
        """Lists all the alerts.

        Args:

            [0], the alert id (optional)

        Example URLs:

            GET /api/v1/alerts
            GET /api/v1/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26
        """

        return self.service.alerts \
            if not args else self.service.alerts[uuid.UUID(args[0])]

    @apimanager.validate(returncode=201, min_args=0, max_args=1)
    def post(self, *args, **kwargs):
        """Create a new alert.

        Args:

            [0], the alert id (optional)

        Request:

            version: protocol version (1.0)
            alert: the alert
        """

        alert_id = uuid.UUID(args[0]) if args else uuid.uuid4()

        if 'alert' in kwargs:
            alert = self.service.create(uuid=alert_id, alert=kwargs['alert'])
        else:
            alert = self.service.create(uuid=alert_id)

        self.set_header("Location", "/api/v1/alerts/%s" % alert.uuid)

    @apimanager.validate(returncode=204, min_args=0, max_args=1)
    def delete(self, *args, **kwargs):
        """Delete one or all alerts.

        Args:

            [0], the alert id (optional)

        Example URLs:

            DELETE /api/v1/alerts
            DELETE /api/v1/alerts/52313ecb-9d00-4b7d-b873-b55d3d9ada26
        """

        if args:
            self.service.remove(uuid.UUID(args[0]))
        else:
            self.service.remove_all()
