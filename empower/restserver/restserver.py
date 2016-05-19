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

"""Exposes a RESTful interface for EmPOWER."""

import tornado.web
import tornado.httpserver

from tornado.web import MissingArgumentError
from uuid import UUID
from empower import settings
from empower.core.account import ROLE_ADMIN, ROLE_USER
from empower.restserver.apihandlers import EmpowerAPIHandler
from empower.main import _do_launch
from empower.main import _parse_args
from empower.main import RUNTIME
from empower.core.tenant import T_TYPES
from empower.core.tenant import T_TYPE_UNIQUE
from empower.datatypes.ssid import SSID
from empower.datatypes.etheraddress import EtherAddress


import empower.logger
LOG = empower.logger.get_logger()

DEFAULT_PORT = 8888


def exceptions(method):
    """Decorator catching the most common exceptions."""

    def magic(self, *args, **kwargs):
        """Perform basic exception catching in rest calls."""

        try:
            method(self, *args, **kwargs)
        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

    return magic


class BaseHandler(tornado.web.RequestHandler):
    """ Base handler, implements only basic authentication stuff. """

    HANDLERS = [r"/"]
    PAGE = "index.html"

    def initialize(self, server=None):
        self.server = server

    def get_current_user(self):
        """ Return username of currently logged user. """

        if self.get_secure_cookie("user"):
            return self.get_secure_cookie("user").decode('UTF-8')
        else:
            return None

    @tornado.web.authenticated
    def get(self):
        """ Render page. """

        try:
            error = self.get_argument("error")
        except MissingArgumentError:
            error = ""

        account = RUNTIME.accounts[self.get_current_user()]

        self.render(self.PAGE,
                    username=self.get_current_user(),
                    password=account.password,
                    name=account.name,
                    surname=account.surname,
                    email=account.email,
                    role=account.role,
                    error=error)


class RequestTenantHandler(BaseHandler):
    """Tenant management (for users)."""

    PAGE = "request_tenant.html"
    HANDLERS = [r"/request_tenant/?"]


class ProfileHandler(BaseHandler):
    """Profile managerment (both read and update)."""

    PAGE = "profile.html"
    HANDLERS = [r"/profile/?"]


class AuthLoginHandler(BaseHandler):
    """Login handler."""

    HANDLERS = [r"/auth/login/?"]

    def get(self):
        try:
            self.render("login.html", error=self.get_argument("error"))
        except MissingArgumentError:
            self.render("login.html", error="")

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        if RUNTIME.check_permission(username, password):
            self.set_secure_cookie("user", username)
            self.redirect(self.get_argument("next", "/"))
        else:
            error_msg = "Login incorrect."
            self.redirect("/auth/login/" +
                          "?error=" +
                          tornado.escape.url_escape(error_msg))


class AuthLogoutHandler(BaseHandler):
    """Logout handler."""

    HANDLERS = [r"/auth/logout/?"]

    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class ManageTenantHandler(BaseHandler):
    """Tenant management (for users)."""

    PAGE = "manage_tenant.html"
    HANDLERS = [r"/manage_tenant/?"]

    @tornado.web.authenticated
    def get(self):
        """ Render page. """

        tenant_id = UUID(self.get_argument("tenant_id", ""))
        tenant = RUNTIME.tenants[tenant_id]

        try:
            error = self.get_argument("error")
        except MissingArgumentError:
            error = ""

        account = RUNTIME.accounts[self.get_current_user()]

        self.render(self.PAGE,
                    username=self.get_current_user(),
                    password=account.password,
                    name=account.name,
                    surname=account.surname,
                    email=account.email,
                    role=account.role,
                    error=error,
                    tenant=tenant)


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

            acl = getattr(RUNTIME, self.STRUCT)

            if len(args) == 0:
                self.write_as_json(acl.values())
            else:
                if EtherAddress(args[0]) in acl:
                    self.write_as_json(EtherAddress(args[0]))
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

            label = ""

            if "label" in request:
                label = request['label']

            func = getattr(RUNTIME, 'add_%s' % self.STRUCT)
            func(EtherAddress(request['sta']), label)

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
            func = getattr(RUNTIME, 'remove_%s' % self.STRUCT)
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


class AccountsHandler(EmpowerAPIHandler):
    """Accounts handler. Used to add/remove accounts."""

    RIGHTS = {'GET': None,
              'POST': [ROLE_ADMIN],
              'PUT': [ROLE_ADMIN, ROLE_USER],
              'DELETE': [ROLE_ADMIN]}

    HANDLERS = [r"/api/v1/accounts/?",
                r"/api/v1/accounts/([a-zA-Z0-9:.]*)/?"]

    def get(self, *args):
        """ Lists either all the accounts running in controller or just
        the one requested. Returns 404 if the requested account does not
        exists.

        Args:
            username: the id of a component istance

        Example URLs:

            GET /api/v1/accounts
            GET /api/v1/accounts/root

        """

        try:
            if len(args) > 1:
                raise ValueError("Invalid url")
            accounts = {}
            for account in RUNTIME.accounts:
                accounts[account] = RUNTIME.accounts[account].to_dict()
            if len(args) == 0:
                self.write_as_json(accounts)
            else:
                self.write_as_json(accounts[args[0]])
        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args, **kwargs):
        """ Create a new account.

        Request:
            version: protocol version (1.0)
            username: username
            password: password
            role: tole
            name: name
            surname: surname
            email: email

        Example URLs:

            POST /api/v1/accounts
            {
              "version" : 1.0,
              "username" : "foo",
              "password" : "foo",
              "role" : "user",
              "name" : "foo",
              "surname" : "foo",
              "email" : "foo@email.com"
            }

        """

        try:

            if len(args) != 0:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "username" not in request:
                raise ValueError("missing username element")

            if "password" not in request:
                raise ValueError("missing password element")

            if "role" not in request:
                raise ValueError("missing role element")

            if "name" not in request:
                raise ValueError("missing name element")

            if "surname" not in request:
                raise ValueError("missing surname element")

            if "email" not in request:
                raise ValueError("missing email element")

            if request['role'] not in [ROLE_ADMIN, ROLE_USER]:
                raise ValueError("Invalid role %s" % request['role'])

            RUNTIME.create_account(request['username'],
                                   request['password'],
                                   request['role'],
                                   request['name'],
                                   request['surname'],
                                   request['email'])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def put(self, *args, **kwargs):
        """ Update an account.

        Args:
            username: the username

        Request:
            version: protocol version (1.0)
            username: username
            password: password
            role: tole
            name: name
            surname: surname
            email: email

        Example URLs:

            PUT /api/v1/accounts/test
            {
              "version" : 1.0,
              "username" : "foo",
              "password" : "foo",
              "role" : "user",
              "name" : "foo",
              "surname" : "foo",
              "email" : "foo@email.com"
            }

        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            del request['version']

            RUNTIME.update_account(args[0], request)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except AttributeError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def delete(self, *args, **kwargs):
        """ Unload a component.

        Args:
            username: the username

        Example URLs:

            DELETE /api/v1/accounts/test

        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid url")

            RUNTIME.remove_account(args[0])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)


class ComponentsHandler(EmpowerAPIHandler):
    """Components handler. Used to load/unload components."""

    HANDLERS = [r"/api/v1/components/?",
                r"/api/v1/components/([a-zA-Z0-9:\-.]*)/?"]

    def get(self, *args):
        """ Lists either all the components running in this controller or just
        the one requested. Returns 404 if the requested component does not
        exists.

        Args:
            component_id: the id of a component istance

        Example URLs:

            GET /api/v1/components
            GET /api/v1/components/<component>

        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid url")

            componets = {}

            for component in RUNTIME.components:

                if hasattr(RUNTIME.components[component], 'to_dict'):
                    componets[component] = \
                        RUNTIME.components[component].to_dict()
                else:
                    componets[component] = {}

            if len(args) == 0:
                self.write_as_json(componets)
            else:
                self.write_as_json(componets[args[0]])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def put(self, *args):
        """ Update a component.

        Args:
            component_id: the id of a component istance

        Request:
            version: protocol version (1.0)
            params: dictionary of parametes supported by the component
                    as reported by the GET request

        Example URLs:

            PUT /api/v1/empower.apps.mobilitymanager. \
                mobilitymanager:52313ecb-9d00-4b7d-b873-b55d3d9ada26
            {
              "version" : 1.0,
              "params" : { "every": 2000 }
            }

        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "params" not in request:
                raise ValueError("missing params element")

            app = RUNTIME.components[args[0]]

            for param in request['params']:
                setattr(app, param, request['params'][param])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def delete(self, *args, **kwargs):
        """ Unload a component.

        Args:
            component_id: the id of a component istance

        Example URLs:

            DELETE /api/v1/components/component

        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid url")

            RUNTIME.unregister(args[0])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def post(self, *args, **kwargs):
        """ Add a component.

        Args:
            component_id: the id of a component istance

        Request:
            version: protocol version (1.0)
            component: module name
            params: dictionary of parametes supported by the component
                    as reported by the GET request

        Example URLs:

            PUT /api/v1/components
            {
              "version" : 1.0,
              "component" : "<component>"
            }

        """

        try:

            if len(args) != 0:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "argv" not in request:
                raise ValueError("missing argv element")

            argv = request['argv'].split(" ")
            components, components_order = _parse_args(argv)

            if not _do_launch(components, components_order):
                raise ValueError("Invalid args")

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)


class PendingTenantHandler(EmpowerAPIHandler):
    """Pending Tenant handler. Used to view and manipulate tenant requests."""

    RIGHTS = {'GET': None,
              'POST': [ROLE_USER],
              'DELETE': [ROLE_ADMIN, ROLE_USER]}

    HANDLERS = [r"/api/v1/pending/?",
                r"/api/v1/pending/([a-zA-Z0-9-]*)/?"]

    def get(self, *args, **kwargs):
        """ Lists all the tenants requested. Returns 404 if the requested
        tenant does not exists.

        Args:
            tenant_id: network name of a tenant

        Example URLs:

            GET /api/v1/pending
            GET /api/v1/pending/TenantName

        """

        try:
            if len(args) > 1:
                raise ValueError("Invalid url")
            if len(args) == 0:
                user = self.get_argument("user", default=None)
                if user:
                    pendings = RUNTIME.load_pending_tenants(user)
                else:
                    pendings = RUNTIME.load_pending_tenants()
                self.write_as_json(pendings)
            else:
                tenant_id = UUID(args[0])
                pending = RUNTIME.load_pending_tenant(tenant_id)
                self.write_as_json(pending)
        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args, **kwargs):
        """ Create a new tenant request.

        Args:
            None

        Request:
            version: protocol version (1.0)
            owner: the username of the requester
            tenant_id: the network name
            desc: a description for the new tenant
            bssid_type: shared or unique

        Example URLs:

            POST /api/v1/pending

        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "desc" not in request:
                raise ValueError("missing desc element")

            if "tenant_name" not in request:
                raise ValueError("missing tenant_name element")

            if "bssid_type" not in request:
                bssid_type = T_TYPE_UNIQUE
            else:
                bssid_type = request['bssid_type']

            if bssid_type not in T_TYPES:
                raise ValueError("invalid bssid_type %s" % bssid_type)

            if len(args) == 1:
                tenant_id = UUID(args[0])
            else:
                tenant_id = None

            tenant_name = SSID(request['tenant_name'])

            RUNTIME.request_tenant(self.account.username,
                                   request['desc'],
                                   tenant_name,
                                   bssid_type,
                                   tenant_id)

            self.set_header("Location", "/api/v1/pendig/%s" % tenant_id)

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """ Delete a tenant request.

        Args:
            tenant_id: network name of a tenant

        Example URLs:

            PUT /api/v1/pending/52313ecb-9d00-4b7d-b873-b55d3d9ada26

        """

        try:

            if len(args) == 0:

                pendings = RUNTIME.load_pending_tenants()

                for pending in pendings:
                    RUNTIME.reject_tenant(pending.tenant_id)

            else:

                tenant_id = UUID(args[0])
                RUNTIME.reject_tenant(tenant_id)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)
        self.set_status(204, None)


class TenantHandler(EmpowerAPIHandler):

    """Tenat handler. Used to view and manipulate tenants."""

    RIGHTS = {'GET': None,
              'POST': [ROLE_ADMIN],
              'DELETE': [ROLE_ADMIN, ROLE_USER]}

    HANDLERS = [r"/api/v1/tenants/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/?"]

    def get(self, *args, **kwargs):
        """ Lists either all the tenants managed by this controller or just the
        one requested. Returns 404 if the requested tenant does not exists.

        Args:
            tenant_id: network name of a tenant

        Example URLs:

            GET /api/v1/tenants
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26

        """

        try:
            if len(args) > 1:
                raise ValueError("Invalid url")
            if len(args) == 0:
                tenants = RUNTIME.tenants.values()
                user = self.get_argument("user", default=None)
                if user:
                    filtered = [x for x in tenants if x.owner == user]
                    self.write_as_json(filtered)
                else:
                    self.write_as_json(tenants)
            else:
                tenant_id = UUID(args[0])
                tenant = RUNTIME.tenants[tenant_id]
                self.write_as_json(tenant)
        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args, **kwargs):
        """ Create a new tenant.

        Args:
            None

        Request:
            version: protocol version (1.0)
            owner: the username of the requester
            tenant_id: the network name
            desc: a description for the new tenant
            bssid_type: shared or unique

        Example URLs:

            POST /api/v1/tenants

        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "owner" not in request:
                raise ValueError("missing owner element")

            if "desc" not in request:
                raise ValueError("missing desc element")

            if "tenant_name" not in request:
                raise ValueError("missing tenant_name element")

            if "bssid_type" not in request:
                bssid_type = T_TYPE_UNIQUE
            else:
                bssid_type = request['bssid_type']

            if bssid_type not in T_TYPES:
                raise ValueError("invalid bssid_type %s" % bssid_type)

            if len(args) == 1:
                tenant_id = UUID(args[0])
            else:
                tenant_id = None

            tenant_name = SSID(request['tenant_name'])

            RUNTIME.add_tenant(request['owner'],
                               request['desc'],
                               tenant_name,
                               bssid_type,
                               tenant_id)

            self.set_header("Location", "/api/v1/tenants/%s" % tenant_id)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """ Delete a tenant.

        Args:
            tenant_id: network name of a tenant

        Request:
            version: protocol version (1.0)

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26

        """
        try:

            if len(args) == 0:

                for tenant in list(RUNTIME.tenants.keys()):
                    RUNTIME.remove_tenant(tenant)

            else:

                tenant_id = UUID(args[0])
                RUNTIME.remove_tenant(tenant_id)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)
        self.set_status(204, None)


class TenantComponentsHandler(EmpowerAPIHandler):
    """Components handler. Used to load/unload components."""

    HANDLERS = \
        [r"/api/v1/tenants/([a-zA-Z0-9-]*)/components/?",
         r"/api/v1/tenants/([a-zA-Z0-9-]*)/components/([a-zA-Z0-9:\-.]*)/?"]

    def get(self, *args):
        """ Lists either all the components running in this controller or just
        the one requested. Returns 404 if the requested component does not
        exists.

        Args:
            tenant_id: the tenant id
            component_id: the id of a component istance

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/<id>

        """

        try:

            if len(args) < 1 or len(args) > 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            if len(args) == 1:
                self.write_as_json(tenant.components)
            else:
                componet_id = args[1]
                self.write_as_json(tenant.components[componet_id])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def put(self, *args):
        """ Update a component.

        Args:
            tenant_id: the tenant id
            component_id: the id of a component istance

        Request:
            version: protocol version (1.0)
            params: dictionary of parametes supported by the component
                    as reported by the GET request

        Example URLs:

            PUT /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/<id>

            {
              "version" : 1.0,
              "params" : { "every": 2000 }
            }

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "params" not in request:
                raise ValueError("missing params element")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            app_id = args[1]
            app = tenant.components[app_id]

            for param in request['params']:
                setattr(app, param, request['params'][param])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def delete(self, *args, **kwargs):
        """ Unload a component.

        Args:
            tenant_id: the tenant id
            component_id: the id of a component istance

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/<id>

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            app_id = args[1]

            RUNTIME.unregister_app(tenant_id, app_id)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)

    def post(self, *args, **kwargs):
        """ Add a component.

        Args:
            tenant_id: the tenant id
            component_id: the id of a component istance

        Request:
            version: protocol version (1.0)
            argv: the app to be loaded
            params: the apps parameters

        Example URLs:

            POST
                /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/components
            {
              "version" : 1.0,
              "argv" : "apps.pollers.linkstatspoller"
            }

        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "argv" not in request:
                raise ValueError("missing argv element")

            tenant_id = UUID(args[0])

            argv = request['argv'].split(" ")
            argv.append("--tenant_id=%s" % tenant_id)

            components, components_order = _parse_args(argv)

            if not _do_launch(components, components_order):
                raise ValueError("Invalid args")

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)


class RESTServer(tornado.web.Application):
    """Exposes the REST API."""

    handlers = [BaseHandler,
                RequestTenantHandler,
                ProfileHandler,
                AuthLoginHandler,
                AuthLogoutHandler,
                ManageTenantHandler,
                AccountsHandler,
                ComponentsHandler,
                TenantComponentsHandler,
                PendingTenantHandler,
                TenantHandler,
                AllowHandler,
                DenyHandler]

    parms = {
        "template_path": settings.TEMPLATE_PATH,
        "static_path": settings.STATIC_PATH,
        "debug": settings.DEBUG,
        "cookie_secret": settings.COOKIE_SECRET,
        "login_url": "/auth/login/"
    }

    def __init__(self, port, cert, key):

        self.port = int(port)
        self.cert = cert
        self.key = key

        handlers = []

        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler))

        tornado.web.Application.__init__(self, handlers, **self.parms)

        if not cert or not key:
            http_server = tornado.httpserver.HTTPServer(self)
        else:
            http_server = tornado.httpserver.HTTPServer(self, ssl_options={
                "certfile": self.cert,
                "keyfile": self.key,
            })

        http_server.listen(self.port)

    def add_handler_class(self, handler_class, server):
        """Add a new handler class."""

        for url in handler_class.HANDLERS:
            self.add_handler((url, handler_class, dict(server=server)))

    def add_handler(self, handler):
        """Add a new handler to the REST server."""

        self.add_handlers(r".*$", [handler])

    def to_dict(self):
        """Return a dict representation of the object."""

        return {'port': self.port,
                'certfile': self.cert,
                'keyfile': self.key}


def launch(port=DEFAULT_PORT, cert=None, key=None):
    """ Start REST Server module. """

    server = RESTServer(int(port), cert, key)
    LOG.info("REST Server available at %u", server.port)
    return server
