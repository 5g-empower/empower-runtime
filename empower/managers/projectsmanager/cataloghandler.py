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

"""Exposes a RESTful interface ."""

import empower.managers.apimanager.apimanager as apimanager


# pylint: disable=W0223
class CatalogHandler(apimanager.EmpowerAPIHandler):
    """Access the applications catalog."""

    URLS = [r"/api/v1/projects/catalog/?"]

    @apimanager.validate(min_args=0, max_args=0)
    def get(self, *args, **kwargs):
        """List of available applications

        Example URLs:

             GET /api/v1/projects/catalog

            {
                empower.apps.wifimobilitymanager.wifimobilitymanager: {
                    params: {
                        service_id: {
                            desc: "The unique UUID of the application.",
                            mandatory: true,
                            type: "UUID"
                        },
                        project_id: {
                            desc: "The project on which this app must
                                be executed.",
                            mandatory: true,
                            type: "UUID"
                        },
                        every: {
                            desc: "The control loop period (in ms).",
                            mandatory: false,
                            default: 2000,
                            type: "int"
                        }
                    },
                    name:
                        "empower.apps.wifimobilitymanager.wifimobilitymanager",
                    desc: "A simple Wi-Fi mobility manager."
                }
            }
        """

        return self.service.catalog
