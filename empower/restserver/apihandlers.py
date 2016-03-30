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

"""Empower common API Handlers."""

import json
import base64
import re
import tornado.web
import tornado.httpserver

from uuid import UUID

from empower.core.account import ROLE_ADMIN, ROLE_USER
from empower.core.jsonserializer import EmpowerEncoder
from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class EmpowerAPIHandler(tornado.web.RequestHandler):
    """ Base class for all the REST call. """

    RIGHTS = {'GET': None,
              'POST': [ROLE_ADMIN],
              'PUT': [ROLE_ADMIN],
              'DELETE': [ROLE_ADMIN]}

    def initialize(self, server=None):
        """Set pointer to actual rest server."""

        self.server = server

    def write_error(self, code, message=None, **kwargs):
        self.set_header('Content-Type', 'application/json')
        if message:
            out = {"message": "%d: %s (%s)" % (code,
                                               self._reason,
                                               str(message))}
            self.finish(json.dumps(out))
        else:
            out = {"message": "%d: %s" % (code, self._reason)}
            self.finish(json.dumps(out))

    def write_as_json(self, value):
        """Return reply as a json document."""

        self.write(json.dumps(value, cls=EmpowerEncoder))

    def prepare(self):
        """Prepare to handler reply."""

        self.set_header('Content-Type', 'application/json')

        if not self.RIGHTS[self.request.method]:
            return

        auth_header = self.request.headers.get('Authorization')

        if auth_header is None or not auth_header.startswith('Basic '):
            self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
            self.send_error(401)
            return

        auth_bytes = bytes(auth_header[6:], 'utf-8')
        auth_decoded = base64.b64decode(auth_bytes).decode()
        username, password = auth_decoded.split(':', 2)

        # account does not exists
        if not RUNTIME.check_permission(username, password):
            self.send_error(401)
            return

        self.account = RUNTIME.get_account(username)

        if self.account.role in self.RIGHTS[self.request.method]:

            if self.account.role == ROLE_ADMIN:
                return

            if self.account.role == ROLE_USER:

                if self.request.uri.startswith("/api/v1/accounts"):

                    pattern = re.compile("/api/v1/accounts/([a-zA-Z0-9:-]*)/?")
                    match = pattern.match(self.request.uri)

                    if match and match.group(1):
                        if match.group(1) in RUNTIME.accounts:
                            account = RUNTIME.accounts[match.group(1)]
                            if self.account.username == account.username:
                                return
                            else:
                                self.send_error(401)
                                return

                    return

                if self.request.uri.startswith("/api/v1/pending"):
                    pattern = re.compile("/api/v1/pending/([a-zA-Z0-9-]*)/?")
                    match = pattern.match(self.request.uri)
                    if match and match.group(1):
                        try:
                            tenant_id = UUID(match.group(1))
                        except:
                            self.send_error(400)
                            return
                        pending = RUNTIME.load_pending_tenant(tenant_id)
                        if pending:
                            if self.account.username == pending.owner:
                                return
                            self.send_error(401)
                            return

                    return

                if self.request.uri.startswith("/api/v1/tenants"):

                    pattern = re.compile("/api/v1/tenants/([a-zA-Z0-9-]*)/?")
                    match = pattern.match(self.request.uri)

                    if match and match.group(1):
                        tenant_id = UUID(match.group(1))
                        if tenant_id in RUNTIME.tenants:
                            tenant = RUNTIME.tenants[tenant_id]
                            if self.account.username == tenant.owner:
                                return
                            self.send_error(401)
                            return

                    return

        self.send_error(401)
        return


class EmpowerAPIHandlerUsers(EmpowerAPIHandler):
    """Base class for User REST handlers."""

    RIGHTS = {'GET': None,
              'POST': [ROLE_USER],
              'PUT': [ROLE_USER],
              'DELETE': [ROLE_USER]}


class EmpowerAPIHandlerAdminUsers(EmpowerAPIHandler):
    """Base class for Admin/User REST handlers."""

    RIGHTS = {'GET': None,
              'PUT': [ROLE_ADMIN, ROLE_USER],
              'POST': [ROLE_ADMIN, ROLE_USER],
              'DELETE': [ROLE_ADMIN, ROLE_USER]}
