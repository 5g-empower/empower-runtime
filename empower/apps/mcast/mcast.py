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

"""Multicast management app."""

import tornado.web
import tornado.httpserver

from empower.core.app import EmpowerApp
from empower.core.app import EmpowerAppHandler
from empower.core.app import EmpowerAppHomeHandler
from empower.core.app import DEFAULT_PERIOD

import empower.logger
LOG = empower.logger.get_logger()


class MCastHandler(EmpowerAppHandler):

    def put(self, *args, **kwargs):
        """Get method handler.

        This method is used by apps in order to export their data structures.
        By default this REST method calls the to_dict() method of the web app
        object and returns its JSON serialization.

        Args:
            None

        Example URLs:

            PUT /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/mcast
        """

        try:

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            print(request)

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(200, None)


class MCastHomeHandler(EmpowerAppHomeHandler):
    pass


class MCast(EmpowerApp):
    """Energy consumption balacing app.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.mcast.mcast:52313ecb-9d00-4b7d-b873-b55d3d9ada26

    """

    MODULE_NAME = "mcast"
    MODULE_HANDLER = MCastHandler
    MODULE_HOME_HANDLER = MCastHomeHandler

    def __init__(self, tenant, **kwargs):

        EmpowerApp.__init__(self, tenant, **kwargs)

    def loop(self):
        """ Periodic job. """

        pass


def launch(tenant, period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return MCast(tenant, every=period)
