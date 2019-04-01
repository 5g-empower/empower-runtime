#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

import uuid
import tornado.web
import tornado.httpserver

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers
from empower.main import RUNTIME


class UEHandler(EmpowerAPIHandlerUsers):
    """UE handler. Used to view UEs (controller-wide)."""

    HANDLERS = [r"/api/v1/ues/?",
                r"/api/v1/ues/([a-zA-Z0-9-]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all UEs or just the specified one.

        Args:
            ue_id: the lvap address

        Example URLs:
            GET /api/v1/ues
            GET /api/v1/ues/123345
        """

        try:
            if len(args) > 1:
                raise ValueError("Invalid URL")
            if not args:
                self.write_as_json(RUNTIME.ues.values())
            else:
                ue = uuid.UUID(args[0])
                self.write_as_json(RUNTIME.ues[ue])
        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(200, None)

    def put(self, *args, **kwargs):
        """ Set the cell for a given UE.

        Args:
            ud_id: the ue id

        Request:
            version: the protocol version (1.0)

        Example URLs:
            PUT /api/v1/ues/97958af4-6f86-4cd2-9e66-2e61ec60dd0f
        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid URL")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            ue_id = uuid.UUID(args[0])
            ue = RUNTIME.ues[ue_id]

            if "cell" in request and "vbs" in request:

                vbs_addr = EtherAddress(request['vbs'])
                vbs = RUNTIME.vbses[vbs_addr]
                pci = int(request['cell']['pci'])
                ue.cell = vbs.cells[pci]

            elif "vbs" in request:

                vbs_addr = EtherAddress(request['vbs'])
                vbs = RUNTIME.vbses[vbs_addr]
                ue.vbs = vbs

            if "slice" in request:

                # Just a slice is admitted.
                ue.slice = request['slice']

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(204, None)
