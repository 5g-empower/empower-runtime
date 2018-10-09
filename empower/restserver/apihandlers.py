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

"""Empower common API Handlers."""

import json
import base64
import re

from uuid import UUID

import tornado.web
import tornado.httpserver

from empower.core.account import ROLE_ADMIN, ROLE_USER
from empower.core.jsonserializer import EmpowerEncoder
from empower.main import RUNTIME

import empower.logger


class EmpowerAPIHandler(tornado.web.RequestHandler):
    """ Base class for all the REST call. """

    RIGHTS = {'GET': None,
              'POST': [ROLE_ADMIN],
              'PUT': [ROLE_ADMIN],
              'DELETE': [ROLE_ADMIN]}

    def initialize(self, server=None):
        """Set pointer to actual rest server."""

        self.server = server
        self.log = empower.logger.get_logger()

    def write_error(self, code, message=None, **kwargs):
        """Write error as JSON message."""

        self.set_header('Content-Type', 'application/json')

        out = {"code": code, "reason": self._reason}

        if message:
            out["message"] = str(message)

        self.finish(json.dumps(out))

    def write_as_json(self, value):
        """Return reply as a json document."""

        self.write(json.dumps(value, sort_keys=True, indent=4,
                              cls=EmpowerEncoder))

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

            if self.request.uri.startswith("/api/v1/accounts"):

                pattern = re.compile("/api/v1/accounts/([a-zA-Z0-9:-]*)/?")
                match = pattern.match(self.request.uri)

                if match and match.group(1):
                    if match.group(1) in RUNTIME.accounts:
                        account = RUNTIME.accounts[match.group(1)]
                        if self.account.username == account.username:
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
              'PUT': [ROLE_ADMIN, ROLE_USER],
              'POST': [ROLE_ADMIN, ROLE_USER],
              'DELETE': [ROLE_ADMIN, ROLE_USER]}
