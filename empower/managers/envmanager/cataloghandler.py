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
    """Access the workers catalog."""

    URLS = [r"/api/v1/catalog/?"]

    @apimanager.validate(min_args=0, max_args=0)
    def get(self, *args, **kwargs):
        """List of available workers.

        Example URLs:

             GET /api/v1/catalog

            [
                {
                    "name":
                        "empower.workers.wifichannelstats.wifichannelstats",
                    "params": {
                        "every": 2000,
                        "project_id": "4cd2bca2-8c28-4e66-9c8a-7cbd1ba4e6f9",
                        "service_id": "0f91e8ad-1c2a-4b06-97f9-e34097c4c1d0"
                    }
                }
            ]
        """

        return self.service.catalog
