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

"""Exposes a RESTful interface for EmPOWER."""

from uuid import UUID
from uuid import uuid4

import tornado.web
import tornado.httpserver

from tornado.web import MissingArgumentError
from empower import settings
from empower.core.service import Service
from empower.core.account import ROLE_ADMIN, ROLE_USER
from empower.restserver.apihandlers import EmpowerAPIHandler
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers
from empower.main import _do_launch
from empower.main import _parse_args
from empower.main import RUNTIME
from empower.core.tenant import T_TYPES
from empower.core.tenant import T_TYPE_UNIQUE
from empower.datatypes.ssid import SSID
from empower.datatypes.plmnid import PLMNID
from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.dpid import DPID
from empower.datatypes.dscp import DSCP
from empower.datatypes.match import Match

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


class EmpowerAppHomeHandler(BaseHandler):
    """Web UI Handler.

    Templates must be put in the /templates/<app name>/ sub-directory. Static
    files must be put in the /static/<app name>/.
    """

    HANDLERS = [r"/apps/tenants/([a-zA-Z0-9-]*)/([a-zA-Z0-9-]*)/?",
                r"/apps/tenants/([a-zA-Z0-9-]*)/([a-zA-Z0-9-]*)/(.*)"]

    def get(self, *args):

        try:

            if len(args) < 2 or len(args) > 3:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            app_name = args[1]

            if len(args) == 2:
                page = "index.html"
            else:
                page = args[2]

            self.render("apps/%s/%s" % (app_name, page), tenant_id=tenant_id)

        except ValueError as ex:
            self.send_error(400, message=ex)


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

            GET /api/v1/allow
            GET /api/v1/allow/11:22:33:44:55:66
        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid URL")

            acl = getattr(RUNTIME, self.STRUCT)

            if not args:
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

            POST /api/v1/allow
        """
        try:

            if not args:
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
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """ Delete entry from ACL.

        Args:
            addr: the station address

        Example URLs:

            DELETE /api/v1/allow/11:22:33:44:55:66
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
            if not args:
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

            if not args:
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


class MarketplaceHandler(EmpowerAPIHandler):
    """Marketplace handler.

    Used to list available apps."""

    HANDLERS = [r"/api/v1/marketplace?",
                r"/api/v1/marketplace/([a-zA-Z0-9:_\-.]*)/?"]

    def get(self, *args):
        """Lists the available system-wide apps.

        Args:
            component_id: the id of a component istance

        Example URLs:
            GET /api/v1/marketplace
            GET /api/v1/marketplace/<app>
        """

        try:

            if len(args) > 1:
                raise ValueError("Invalid url")

            apps = RUNTIME.load_apps()

            if not args:
                self.write_as_json(apps)
            else:
                self.write_as_json(apps[args[0]])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)


class ComponentsHandler(EmpowerAPIHandler):
    """Components handler. Used to load/unload components."""

    HANDLERS = [r"/api/v1/components/?",
                r"/api/v1/components/([a-zA-Z0-9:_\-.]*)/?"]

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

            if not args:
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

            if not args:
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
            if not args:
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

            bssid_type = T_TYPE_UNIQUE
            if "bssid_type" in request:
                bssid_type = request['bssid_type']

            if "plmn_id" in request:
                plmn_id = PLMNID(request['plmn_id'])
            else:
                plmn_id = None

            if len(args) == 1:
                tenant_id = UUID(args[0])
            else:
                tenant_id = None

            tenant_name = SSID(request['tenant_name'])

            RUNTIME.request_tenant(self.account.username,
                                   request['desc'],
                                   tenant_name,
                                   bssid_type,
                                   tenant_id,
                                   plmn_id)

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

            if not args:

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
            if not args:
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

            bssid_type = T_TYPE_UNIQUE
            if "bssid_type" in request:
                bssid_type = request['bssid_type']

            if bssid_type not in T_TYPES:
                raise ValueError("invalid bssid_type %s" % bssid_type)

            if "plmn_id" in request:
                plmn_id = PLMNID(request['plmn_id'])
            else:
                plmn_id = None

            if len(args) == 1:
                tenant_id = UUID(args[0])
            else:
                tenant_id = None

            tenant_name = SSID(request['tenant_name'])

            RUNTIME.add_tenant(request['owner'],
                               request['desc'],
                               tenant_name,
                               bssid_type,
                               tenant_id,
                               plmn_id)

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

            if not args:

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


class TenantComponentsHandler(EmpowerAPIHandlerUsers):
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

            argv = request['argv'].strip().split(" ")
            argv.append("--tenant_id=%s" % tenant_id)

            components, components_order = _parse_args(argv)

            if not _do_launch(components, components_order):
                raise ValueError("Invalid args")

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)


class TenantSliceHandler(EmpowerAPIHandlerUsers):
    """Tenat slice handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/slices/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/slices/([a-zA-Z0-9-]*)/?"]

    def get(self, *args, **kwargs):
        """List slices.

        Args:
            tenant_id: network name of a tenant
            dscp: the slice DSCP

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/slices
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/slices/ \
              0x40
        """

        try:

            if len(args) < 1 or len(args) > 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            if len(args) == 1:
                self.write_as_json(tenant.slices.values())
            else:
                dscp = DSCP(args[1])
                self.write_as_json(tenant.slices[dscp])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args, **kwargs):
        """Add a new slice.

        Args:
            tenant_id: network name of a tenant
            dscp: the slice DSCP (optional)

        Example URLs:

            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/slices
            {
                "version" : 1.0,
                "aggregation" : true,
                "quantum" : 1500,
                "dscp": "0x42"
            }

        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "amsdu_aggregation" not in request:
                raise ValueError("missing amsdu_aggregation element")

            if "quantum" not in request:
                raise ValueError("missing quantum element")

            if "dscp" not in request:
                raise ValueError("missing dscp element")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            dscp = DSCP(request["dscp"])

            tenant.add_slice(dscp, request["quantum"],
                             request["amsdu_aggregation"])

            url = "/api/v1/tenants/%s/slices/%s" % (tenant_id, dscp)
            self.set_header("Location", url)

        except TypeError as ex:
            self.send_error(400, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def put(self, *args, **kwargs):
        """Modify slice.

        Args:
            tenant_id: network name of a tenant
            dscp: the slice DSCP (optional)

        Example URLs:

            PUT /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/slices/
              0x40
            {
                "version" : 1.0,
                "aggregation" : true,
                "quantum" : 1500
            }

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "amsdu_aggregation" not in request:
                raise ValueError("missing amsdu_aggregation element")

            if "quantum" not in request:
                raise ValueError("missing quantum element")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            dscp = DSCP(args[1])

            tenant.set_slice(dscp, request["quantum"],
                             request["amsdu_aggregation"])

        except TypeError as ex:
            self.send_error(400, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """Delete slice.

        Args:
            tenant_id: network name of a tenant
            dscp: the slice DSCP

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/slice/
              0x40

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            dscp = DSCP(args[1])

            tenant.del_slice(dscp)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)


class TenantEndpointHandler(EmpowerAPIHandlerUsers):
    """TenantEndpointHandler Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps/([a-zA-Z0-9-]*)/?"]

    def get(self, *args, **kwargs):
        """ List all Functions.

        Args:
            tenant_id: the network names of the tenant
            endpoint_id: the endpoint uuid

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/eps
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            if len(args) == 1:
                self.write_as_json(tenant.endpoints.values())
                self.set_status(200, None)
            else:
                endpoint_id = UUID(args[1])
                endpoint = tenant.endpoints[endpoint_id]
                self.write_as_json(endpoint)
                self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args):
        """Add a new Endpoint.

        Args:
            tenant_id: network name of a tenant
            endpoint_id: the endpoint id

        Request:
            version: protocol version (1.0)
            endpoint_name: the endpoint name
            dpid: the datapath id
            ports: a dictionary of VirtualPorts, where each key is a vport_id
                port_id: the port number on the datapath id
                properties: a dictionary of additional information
                    dont_learn: list of hardware addresses bounded to this port

        Example URLs:

            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/eps
            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34
        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "endpoint_name" not in request:
                raise ValueError("missing endpoint_name element")

            if "dpid" not in request:
                raise ValueError("missing dpid element")

            if "ports" not in request:
                raise ValueError("missing ports element")

            if not isinstance(request["ports"], dict):
                raise ValueError("ports is not a dictionary")

            for port in request["ports"].values():

                if "port_id" not in port:
                    raise ValueError("missing port_id element")

            tenant_id = UUID(args[0])

            if tenant_id not in RUNTIME.tenants:
                raise KeyError(tenant_id)

            tenant = RUNTIME.tenants[tenant_id]

            if len(args) == 1:
                endpoint_id = uuid4()
            else:
                endpoint_id = UUID(args[1])

            dpid = DPID(request["dpid"])
            datapath = RUNTIME.datapaths[dpid]

            tenant.add_endpoint(endpoint_id=endpoint_id,
                                endpoint_name=request["endpoint_name"],
                                datapath=datapath,
                                ports=request["ports"])

            self.set_header("Location", "/api/v1/tenants/%s/eps/%s"
                            % (tenant_id, endpoint_id))

        except ValueError as ex:
            self.send_error(400, message=ex)

        except RuntimeError as ex:
            self.send_error(400, message=ex)

        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """ Remove an lvnf from a Tenant.

        Args:
            tenant_id: network name of a tenant
            endpoint_id: the endpoint_id

        Example URLs:

            Delete /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])

            if tenant_id not in RUNTIME.tenants:
                raise KeyError(tenant_id)

            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = UUID(args[1])

            tenant.remove_endpoint(endpoint_id)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)


class TenantEndpointNextHandler(EmpowerAPIHandlerUsers):
    """Tenant/Endpoint/Port/Next Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps" +
                r"/([a-zA-Z0-9-]*)/ports/([0-9]*)/next/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps" +
                r"/([a-zA-Z0-9-]*)/ports/([0-9]*)/next/([a-zA-Z0-9_:,=]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """List next associations.

        Args:
            [0]: the tenant id
            [1]: the endpoint id
            [2]: the port id
            [3]: match

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next/
                in_port=1,dl_type=800,nw_proto=84
        """

        try:

            if len(args) not in [3, 4]:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = UUID(args[1])
            endpoint = tenant.endpoints[endpoint_id]

            port_id = int(args[2])
            port = endpoint.ports[port_id]

            if len(args) == 3:
                self.write_as_json(port.next)
            else:
                match = args[3]
                self.write_as_json(port.next[match])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(200, None)

    def post(self, *args, **kwargs):
        """Set next flow rules.

        Args:
            [0]: the tenant id
            [1]: the endpoint id
            [2]: the port id

        Example URLs:

            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next
        """

        try:

            if len(args) != 3:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "match" not in request:
                raise ValueError("missing match element")

            if "next" not in request:
                raise ValueError("missing next element")

            match = request['match']

            if not isinstance(match, str):
                raise ValueError("Field match must be a string")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = UUID(args[1])
            endpoint = tenant.endpoints[endpoint_id]

            port_id = int(args[2])
            port = endpoint.ports[port_id]

            next_type = request['next']['type'].lower()
            next_id = UUID(request['next']['uuid'])

            valid_types = ["lvnf", "ep"]

            if next_type not in valid_types:
                raise ValueError("invalid type, allowed are %s" % valid_types)

            next_obj = None
            if next_type == "lvnf":
                next_obj = tenant.lvnfs[next_id]
            elif next_type == "ep":
                next_obj = tenant.endpoints[next_id]

            if next_id == endpoint_id:
                raise ValueError("Loop detected")

            next_port_id = int(request['next']['port_id'])
            next_port = next_obj.ports[next_port_id]

            port.next[match] = next_port

            url = "/api/v1/tenants/%s/eps/%s/ports/%u/next/%s"
            tokens = (tenant_id, endpoint_id, port_id, match)

            self.set_header("Location", url % tokens)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """Delete next flow rules.

        Args:
            [0]: the tenant id
            [1]: the endpoint id
            [2]: the port id
            [3]: match

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                   eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1/next/
                   dl_src=00:18:DE:CC:D3:40;dpid=00:0D:B9:2F:56:64;port_id=2
        """

        try:

            if len(args) not in [3, 4]:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = UUID(args[1])
            endpoint = tenant.endpoints[endpoint_id]

            port_id = int(args[2])
            port = endpoint.ports[port_id]

            if len(args) == 4:
                match = args[3]
            else:
                match = ""

            del port.next[match]

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)


class TenantEndpointPortHandler(EmpowerAPIHandlerUsers):
    """Tenant/Endpoint/Port Handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps" +
                "/([a-zA-Z0-9-]*)/ports/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/eps" +
                "/([a-zA-Z0-9-]*)/ports/([0-9]*)/?"]

    def initialize(self, server):
        self.server = server

    def get(self, *args, **kwargs):
        """ List all ports.

        Args:
            [0]: the tenant id
            [1]: the endpoint id
            [2]: the port id

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
                eps/49313ecb-9d00-4a7c-b873-b55d3d9ada34/ports/1
        """

        try:

            if len(args) > 3 or len(args) < 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            endpoint_id = UUID(args[1])
            endpoint = tenant.endpoints[endpoint_id]

            if len(args) == 2:
                self.write_as_json(endpoint.ports.values())
                self.set_status(200, None)
            else:
                port_id = int(args[2])
                port = endpoint.ports[port_id]
                self.write_as_json(port)
                self.set_status(200, None)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)


class TenantTrafficHandler(EmpowerAPIHandlerUsers):
    """Tenat traffic rule queue handler."""

    HANDLERS = [r"/api/v1/tenants/([a-zA-Z0-9-]*)/trs/?",
                r"/api/v1/tenants/([a-zA-Z0-9-]*)/trs/([a-zA-Z0-9_=,]*)/?"]

    def get(self, *args, **kwargs):
        """List traffic rules .

        Args:
            tenant_id: network name of a tenant
            match: the openflow match rule (e.g. dl_vlan=100;tp_dst=80)

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/trs
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/trs/ \
              dl_vlan=100;tp_dst=80
        """

        try:

            if len(args) not in [1, 2]:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            if len(args) == 1:
                self.write_as_json(tenant.traffic_rules.values())
            else:
                match = Match(args[1])
                self.write_as_json(tenant.traffic_rules[match])

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

    def post(self, *args, **kwargs):
        """Add traffic rule.

        Args:
            tenant_id: network name of a tenant

        Example URLs:

            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/slices
            {
                "version" : 1.0,
                "dscp" : 0x40,
                "label" : "video traffic (high priority)",
                "match" : "dl_vlan=100;tp_dst=80",
            }

        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid url")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "dscp" not in request:
                raise ValueError("missing dscp element")

            if "label" not in request:
                raise ValueError("missing label element")

            if "match" not in request:
                raise ValueError("missing match element")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            dscp = DSCP(request["dscp"])
            match = Match(request["match"])

            tenant.add_traffic_rule(match, dscp, request["label"])

            url = "/api/v1/tenants/%s/trs/%s" % (tenant_id, match)
            self.set_header("Location", url)

        except TypeError as ex:
            self.send_error(400, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(201, None)

    def delete(self, *args, **kwargs):
        """Delete traffic rule queues.

        Args:
            tenant_id: network name of a tenant

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/trs/ \
              dl_vlan=100;tp_dst=80

        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid url")

            tenant_id = UUID(args[0])
            tenant = RUNTIME.tenants[tenant_id]

            match = Match(args[1])

            tenant.del_traffic_rule(match)

        except ValueError as ex:
            self.send_error(400, message=ex)
        except KeyError as ex:
            self.send_error(404, message=ex)

        self.set_status(204, None)


class RESTServer(Service, tornado.web.Application):
    """Exposes the REST API."""

    parms = {
        "template_path": settings.TEMPLATE_PATH,
        "static_path": settings.STATIC_PATH,
        "debug": settings.DEBUG,
        "cookie_secret": settings.COOKIE_SECRET,
        "login_url": "/auth/login/"
    }

    def __init__(self, port, cert, key):

        Service.__init__(self, every=-1)

        self.port = int(port)
        self.cert = cert
        self.key = key

        tornado.web.Application.__init__(self, [], **self.parms)

        if not cert or not key:
            http_server = tornado.httpserver.HTTPServer(self)
        else:
            http_server = tornado.httpserver.HTTPServer(self, ssl_options={
                "certfile": self.cert,
                "keyfile": self.key,
            })

        http_server.listen(self.port)

        handler_classes = [BaseHandler, EmpowerAppHomeHandler,
                           RequestTenantHandler, ProfileHandler,
                           AuthLoginHandler, AuthLogoutHandler,
                           ManageTenantHandler, AccountsHandler,
                           ComponentsHandler, TenantComponentsHandler,
                           PendingTenantHandler, TenantHandler,
                           AllowHandler, TenantSliceHandler,
                           TenantEndpointHandler, TenantEndpointNextHandler,
                           TenantEndpointPortHandler, TenantTrafficHandler,
                           MarketplaceHandler]

        for handler_class in handler_classes:
            self.add_handler_class(handler_class, http_server)

    def add_handler_class(self, handler_class, server):
        """Add a new handler class."""

        for url in handler_class.HANDLERS:
            self.add_handler((url, handler_class, dict(server=server)))

    def add_handler(self, handler):
        """Add a new handler to the REST server."""

        self.add_handlers(r".*$", [handler])

    def to_dict(self):
        """Return a dict representation of the object."""

        out = Service.to_dict(self)
        out['port'] = self.port
        out['certfile'] = self.cert
        out['keyfile'] = self.key

        return out


def launch(port=DEFAULT_PORT, cert=None, key=None):
    """ Start REST Server module. """

    server = RESTServer(int(port), cert, key)
    server.log.info("REST Server available at %u", server.port)
    return server
