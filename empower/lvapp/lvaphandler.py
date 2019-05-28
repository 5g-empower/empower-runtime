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

"""LVAPs Handerler."""

import tornado.web
import tornado.httpserver

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandler
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import REVERSE_BANDS

from empower.main import RUNTIME


class LVAPHandler(EmpowerAPIHandler):
    """LVAP handler. Used to view LVAPs (controller-wide)."""

    HANDLERS = [r"/api/v1/lvaps/?",
                r"/api/v1/lvaps/([a-zA-Z0-9:]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all LVAPs or just the specified one.

        Args:
            lvap_id: the lvap address

        Example URLs:
            GET /api/v1/lvaps
            GET /api/v1/lvaps/11:22:33:44:55:66
        """

        try:
            if len(args) > 1:
                raise ValueError("Invalid URL")
            if not args:
                self.write_as_json(RUNTIME.lvaps.values())
            else:
                lvap = EtherAddress(args[0])
                self.write_as_json(RUNTIME.lvaps[lvap])
        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(200, None)

    def put(self, *args, **kwargs):
        """ Set the WTP for a given LVAP, effectivelly hands-over the LVAP to
        another WTP

        Args:
            lvap_id: the lvap address

        Request:
            version: the protocol version (1.0)

        Example URLs:
            PUT /api/v1/lvaps/11:22:33:44:55:66
        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid URL")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            lvap_addr = EtherAddress(args[0])

            lvap = RUNTIME.lvaps[lvap_addr]

            if "blocks" in request:

                pool = []

                for block in request["blocks"]:

                    wtp_addr = EtherAddress(block['wtp'])
                    wtp = RUNTIME.wtps[wtp_addr]
                    hwaddr = EtherAddress(block['hwaddr'])
                    channel = int(block['channel'])
                    band = block['band']

                    r_block = ResourceBlock(wtp, hwaddr, channel, REVERSE_BANDS[band])
                    pool.append(r_block)

                lvap.blocks = pool

            elif "wtp" in request:

                wtp_addr = EtherAddress(request['wtp'])
                wtp = RUNTIME.wtps[wtp_addr]
                lvap.wtp = wtp

            if "encap" in request:

                encap = EtherAddress(request["encap"])
                lvap.encap = encap

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(204, None)
