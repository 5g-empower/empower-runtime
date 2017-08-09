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
import uuid

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers
from empower.core.resourcepool import ResourceBlock

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class TenantLVAPHandler(EmpowerAPIHandlerUsers):
    """TenantLVAP handler. Used to view and manipulate LVAPs in tenants."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvaps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/lvaps/([a-zA-Z0-9:]*)/?"]

    def get(self, *args, **kwargs):
        """ Get all LVAPs in a Pool or just the specified one.

        Args:
            pool_id: the network name
            lvap_id: the lvap address

        Example URLs:
            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvaps
            GET /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvaps/11:22:33:44:55:66
        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid URL")

            tenant_id = uuid.UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]
            lvaps = tenant.lvaps

            if len(args) == 1:
                self.write_as_json(lvaps.values())
            else:
                lvap = EtherAddress(args[1])
                self.write_as_json(lvaps[lvap])

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(200, None)

    def put(self, *args, **kwargs):
        """ Set the WTP for a given LVAP, effectivelly hands-over the LVAP to
        another WTP

        Args:
            pool_id: the pool address
            lvap_id: the lvap address

        Request:
            version: the protocol version (1.0)

        Example URLs:
            PUT /api/v1/pools/52313ecb-9d00-4b7d-b873-b55d3d9ada26/lvaps/11:22:33:44:55:66
        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid URL")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            tenant_id = uuid.UUID(args[0])
            lvap_addr = EtherAddress(args[1])

            tenant = RUNTIME.tenants[tenant_id]
            lvap = tenant.lvaps[lvap_addr]

            if "wtp" in request:

                wtp_addr = EtherAddress(request['wtp'])
                wtp = tenant.wtps[wtp_addr]
                lvap.wtp = wtp

            elif "blocks" in request:

                pool = []

                for block in request["blocks"]:

                    wtp_addr = EtherAddress(block['wtp'])
                    wtp = RUNTIME.wtps[wtp_addr]
                    hwaddr = EtherAddress(block['hwaddr'])
                    channel = int(block['channel'])
                    band = int(block['band'])

                    r_block = ResourceBlock(wtp, hwaddr, channel, band)
                    pool.append(r_block)

                lvap.blocks = pool

            if "encap" in request:

                encap = EtherAddress(request["encap"])
                lvap.encap = encap

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(204, None)
