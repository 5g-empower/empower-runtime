#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""LVAPs Handerler."""

import tornado.web
import tornado.httpserver
import uuid

from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool

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
            GET /api/v1/pools/EmPOWER/lvaps
            GET /api/v1/pools/EmPOWER/lvaps/11:22:33:44:55:66
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
            wtp: the new wtp address

        Example URLs:
            PUT /api/v1/pools/EmPOWER/lvaps/11:22:33:44:55:66
        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid URL")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "wtp" not in request and "scheduled_on" not in request and \
               "encap" not in request:

                raise ValueError("missing wtp/scheduled_on element")

            tenant_id = uuid.UUID(args[0])
            lvap_addr = EtherAddress(args[1])

            tenant = RUNTIME.tenants[tenant_id]
            lvap = tenant.lvaps[lvap_addr]

            if "wtp" in request:

                wtp_addr = EtherAddress(request['wtp'])
                wtp = tenant.wtps[wtp_addr]
                lvap.wtp = wtp

            if "scheduled_on" in request:

                pool = ResourcePool()

                for block in request["scheduled_on"]:

                    wtp_addr = EtherAddress(block['wtp'])
                    wtp = RUNTIME.wtps[wtp_addr]
                    channel = int(block['channel'])
                    band = int(block['band'])

                    rb = ResourceBlock(wtp, channel, band)
                    pool.add(rb)

                lvap.scheduled_on = pool

            if "encap" in request:

                encap = EtherAddress(request["encap"])
                lvap.encap = encap

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(204, None)
