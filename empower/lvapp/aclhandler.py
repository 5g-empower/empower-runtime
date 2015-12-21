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

""" Charybdis ACL Handerlers. """

import tornado.web
import tornado.httpserver
import json

from empower.core.jsonserializer import EmpowerEncoder
from empower.datatypes.etheraddress import EtherAddress
from empower.core.restserver import EmpowerAPIHandler

import empower.logger
LOG = empower.logger.get_logger()


class ACLHandler(EmpowerAPIHandler):

    """ACL handler. Used to view and manipulate the ACL."""

    STRUCT = None
    HANDLERS = []

    def get(self, *args, **kwargs):
        """ List the entire ACL or just the specified entry.

        Args:
            addr: the station address

        Example URLs:

            GET /api/v1/[allow|deny]
            GET /api/v1/[allow|deny/11:22:33:44:55:66
        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid URL")

            acl = getattr(self.server, self.STRUCT)

            if len(args) == 0:
                self.write(json.dumps(acl, cls=EmpowerEncoder))
            else:
                if EtherAddress(args[0]) in acl:
                    json.dumps(EtherAddress(args[0]), cls=EmpowerEncoder)
                else:
                    raise KeyError(EtherAddress(args[0]))

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

    def post(self, *args, **kwargs):
        """ Add new entry to ACL.

        Args:
            None

        Request:
            version: protocol version (1.0)
            sta: the station address

        Example URLs:

            POST /api/v1/[allow|deny]
        """
        try:

            if len(args) != 0:
                raise ValueError("Invalid URL")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "sta" not in request:
                raise ValueError("missing sta element")

            func = getattr(self.server, 'add_%s' % self.STRUCT)
            func(EtherAddress(request['sta']))

            self.set_header("Location", "/api/v1/allow/%s" % request['sta'])

        except KeyError as ex:
            print(ex)
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """ Delete entry from ACL.

        Args:
            addr: the station address

        Example URLs:

            DELETE /api/v1/[allow|deny]/11:22:33:44:55:66
        """

        try:
            if len(args) != 1:
                raise ValueError("Invalid URL")
            func = getattr(self.server, 'remove_%s' % self.STRUCT)
            func(EtherAddress(args[0]))
        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(204, None)


class AllowHandler(ACLHandler):
    """ Allow handler. """

    STRUCT = "allowed"
    HANDLERS = [r"/api/v1/allow/?",
                r"/api/v1/allow/([a-zA-Z0-9:]*)/?"]


class DenyHandler(ACLHandler):
    """ Deny handler. """

    STRUCT = "denied"
    HANDLERS = [r"/api/v1/deny/?",
                r"/api/v1/deny/([a-zA-Z0-9:]*)/?"]
