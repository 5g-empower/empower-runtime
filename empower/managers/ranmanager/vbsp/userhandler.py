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

"""Users Handlers."""

import empower_core.apimanager.apimanager as apimanager


# pylint: disable=W0223
class UserHandler(apimanager.APIHandler):
    """Handler for accessing Users."""

    URLS = [r"/api/v1/users/?",
            r"/api/v1/users/([0-9]*)/?"]

    @apimanager.validate(max_args=1)
    def get(self, *args, **kwargs):
        """List the users.

        Args:

            [0]: the UE IMSI(optional)

        Example URLs:

            GET /api/v1/users

            {
                "222930100001114": {
                    "imsi": 222930100001114,
                    "tmsi": 12643,
                    "rnti": 71,
                    "cell": {
                        "addr": "00:00:00:00:01:9B",
                        "pci": 3,
                        "dl_earfcn": 3400,
                        "ul_earfcn": 21400,
                        "n_prbs": 25,
                        "cell_measurements": {},
                        "ue_measurements": {}
                    },
                    "plmnid": "22293",
                    "status": "connected"
                }
            }

            GET /api/v1/users/222930100001114

            {
                "imsi": 222930100001114,
                "tmsi": 12643,
                "rnti": 71,
                "cell": {
                    "addr": "00:00:00:00:01:9B",
                    "pci": 3,
                    "dl_earfcn": 3400,
                    "ul_earfcn": 21400,
                    "n_prbs": 25,
                    "cell_measurements": {},
                    "ue_measurements": {}
                },
                "plmnid": "22293",
                "status": "connected"
            }
        """

        return self.service.users \
            if not args else self.service.users[int(args[0])]
