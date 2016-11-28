#!/usr/bin/env python3
#
# Copyright (c) 2016 Supreeth Herle
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

"""UEs Handerler."""

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerAdminUsers
from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class UEHandler(EmpowerAPIHandlerAdminUsers):
    """UE handler. Used to view UEs in a VBS (controller-wide)."""

    HANDLERS = [r"/api/v1/ues/?",
                r"/api/v1/ues/([a-zA-Z0-9:]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all UEs or just the specified one.

        Args:
            vbs_id: the vbs identifier
            rnti: the radio network temporary identifier

        Example URLs:
            GET /api/v1/ues
            GET /api/v1/ues/11:22:33:44:55:66
        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid URL")

            if len(args) == 0:
                self.write_as_json(RUNTIME.ues.values())
            else:
                ue_addr = EtherAddress(args[0])
                print(RUNTIME.ues.keys())
                self.write_as_json(RUNTIME.ues[ue_addr])

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(200, None)
