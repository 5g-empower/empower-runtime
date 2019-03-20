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

"""EmPOWER Runtime."""

from random import randint

import pkgutil
import socket
import fcntl
import struct
import tornado.ioloop

from construct import Container
from construct import Struct
from construct import UBInt16
from construct import Bytes

from sqlalchemy.exc import IntegrityError

from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.dscp import DSCP
from empower.persistence import Session
from empower.persistence.persistence import TblTenant
from empower.persistence.persistence import TblAccount
from empower.core.account import Account
from empower.core.account import ROLE_ADMIN
from empower.core.account import ROLE_USER
from empower.core.tenant import Tenant
from empower.core.acl import ACL
from empower.persistence.persistence import TblAllow
from empower.core.tenant import T_TYPES

import empower.logger
import empower.apps

DEFAULT_PERIOD = 5000

CTRL_ADV = Struct("ctrl_adv", Bytes("dst", 6),
                  Bytes("src", 6),
                  UBInt16("eth_type"),
                  Bytes("ctrl", 4),
                  UBInt16("port"))


def generate_default_accounts():
    """Generate default accounts.

    Three default accounts (one root account and two user accounts are created
    the first time the controller is started.
    """

    if not Session().query(TblAccount).all():

        session = Session()
        session.add(TblAccount(username="root",
                               password="root",
                               role="admin",
                               name="Administrator",
                               surname="",
                               email="admin@empower.net"))
        session.add(TblAccount(username="foo",
                               password="foo",
                               role="user",
                               name="Foo",
                               surname="",
                               email="foo@empower.net"))
        session.add(TblAccount(username="bar",
                               password="bar",
                               role="user",
                               name="Bar",
                               surname="",
                               email="bar@empower.net"))
        session.commit()


class EmpowerRuntime:
    """EmPOWER Runtime."""

    def __init__(self, options):

        self.components = {}
        self.accounts = {}
        self.tenants = {}
        self.lvaps = {}
        self.ues = {}
        self.wtps = {}
        self.cpps = {}
        self.vbses = {}
        self.datapaths = {}
        self.allowed = {}
        self.log = empower.logger.get_logger()

        self.log.info("Starting EmPOWER Runtime")

        # generate default users if database is empty
        self.log.info("Generating default accounts")
        generate_default_accounts()

        # load defaults
        self.log.info("Loading EmPOWER Runtime defaults")
        self.__load_accounts()
        self.__load_tenants()
        self.__load_acl()

        if options.ctrl_adv:
            self.__ifname = options.ctrl_adv_iface
            self.__ctrl_ip = options.ctrl_ip
            self.__ctrl_port = options.ctrl_port
            self.__start_adv()

    def __start_adv(self):
        """Star ctrl advertising."""

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        ifname = struct.pack('256s', self.__ifname[:15].encode('utf-8'))
        info = fcntl.ioctl(sock.fileno(), 0x8927, ifname)

        src = EtherAddress(':'.join(['%02x' % char for char in info[18:24]]))
        dst = EtherAddress("FF:FF:FF:FF:FF:FF")

        adv = Container(dst=dst.to_raw(),
                        src=src.to_raw(),
                        eth_type=0xEEEE,
                        ctrl=self.__ctrl_ip.packed,
                        port=self.__ctrl_port)

        self.__msg = CTRL_ADV.build(adv)

        self.__auto_cfg = \
            tornado.ioloop.PeriodicCallback(self.__auto_cfg_loop, 2000)

        self.__auto_cfg.start()

    def __auto_cfg_loop(self):
        """Send ctrl advertisement."""

        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        sock.bind((self.__ifname, 0))
        sock.send(self.__msg)

    def __load_accounts(self):
        """Load accounts table."""

        for account in Session().query(TblAccount).all():

            self.accounts[account.username] = Account(account.username,
                                                      account.password,
                                                      account.name,
                                                      account.surname,
                                                      account.email,
                                                      account.role)

    def __load_tenants(self):
        """Load Tenants."""

        for tenant in Session().query(TblTenant).all():

            if tenant.tenant_id in self.tenants:
                raise KeyError(tenant.tenant_id)

            self.tenants[tenant.tenant_id] = \
                Tenant(tenant.tenant_id,
                       tenant.tenant_name,
                       tenant.owner,
                       tenant.desc,
                       tenant.bssid_type,
                       tenant.plmn_id)

    def __load_acl(self):
        """ Load ACL list. """

        for allow in Session().query(TblAllow).all():

            if allow.addr in self.allowed:
                raise ValueError(allow.addr_str)

            acl = ACL(allow.addr, allow.label)
            self.allowed[allow.addr] = acl

    def load_main_components(self):
        """Fetch the available components.

        A main component is a standard python module defining in the init file
        a python dictionary named MANIFEST.

        The MANIFEST provides:
          - name: the name of the module
          - desc: a human readable description of the app
          - params: the list of parameters defined by the app.

        For each parameter the following info are provided:
          - label: the name of the parameters
          - desc: a description of the parameter
          - mandatory (optional): true/false (default: false)
          - default: the default value of the parameter
        """

        components = {}

        self.__walk_module(empower, components)
        self.__walk_module(empower.lvapp, components)
        self.__walk_module(empower.lvnfp, components)
        self.__walk_module(empower.vbsp, components)

        for component in components:
            if component in self.components:
                components[component]['active'] = True
                if "params" in components[component]:
                    for param in components[component]["params"]:
                        components[component][param] = \
                            getattr(self.components[component], param)
            else:
                components[component]['active'] = False

        return components

    def load_user_components(self, tenant_id):
        """Fetch the available user components.

        A user component is a standard python module defining in the init file
        a python dictionary named MANIFEST.

        The MANIFEST provides:
          - name: the name of the module
          - desc: a human readable description of the app
          - params: the list of parameters defined by the app.

        For each parameter the following info are provided:
          - label: the name of the parameters
          - desc: a description of the parameter
          - mandatory (optional): true/false (default: false)
          - default: the default value of the parameter
        """

        tenant = self.tenants[tenant_id]
        components = {}

        self.__walk_module(empower.apps, components)

        for component in components:
            if component in tenant.components:
                components[component]['active'] = True
                if "params" in components[component]:
                    for param in components[component]["params"]:
                        components[component][param] = \
                            getattr(tenant.components[component], param)
            else:
                components[component]['active'] = False

        return components

    @classmethod
    def __walk_module(cls, package, results):

        pkgs = pkgutil.walk_packages(package.__path__)

        for _, module_name, is_pkg in pkgs:

            __import__(package.__name__ + "." + module_name)

            if not is_pkg:
                continue

            if not hasattr(package, module_name):
                continue

            module = getattr(package, module_name)

            if not hasattr(module, "MANIFEST"):
                continue

            manifest = getattr(module, "MANIFEST")

            name = manifest['name']
            results[name] = manifest

    def add_allowed(self, sta_addr, label=None):
        """ Add entry to ACL. """

        allow = Session().query(TblAllow) \
                         .filter(TblAllow.addr == sta_addr) \
                         .first()
        if allow:
            raise ValueError("Address already defined %s" % sta_addr)

        session = Session()
        session.add(TblAllow(addr=sta_addr, label=label))
        session.commit()

        acl = ACL(sta_addr, label)
        self.allowed[sta_addr] = acl

        return acl

    def remove_allowed(self, sta_addr):
        """ Remove entry from ACL. """

        allow = Session().query(TblAllow) \
                         .filter(TblAllow.addr == sta_addr) \
                         .first()
        if not allow:
            raise KeyError("Address not found %s" % sta_addr)

        session = Session()
        session.delete(allow)
        session.commit()

        del self.allowed[sta_addr]

    def is_allowed(self, src):
        """ Check if station is allowed. """

        return src in self.allowed

    def create_account(self, username, password, role, name, surname, email):
        """Create a new account."""

        if username in self.accounts:
            raise ValueError("%s already registered" % username)

        if role not in [ROLE_ADMIN, ROLE_USER]:
            raise ValueError("Invalid role %s" % role)

        session = Session()
        account = TblAccount(username=username,
                             password=password,
                             role=role,
                             name=name,
                             surname=surname,
                             email=email)

        session.add(account)
        session.commit()

        self.accounts[account.username] = Account(account.username,
                                                  account.password,
                                                  account.name,
                                                  account.surname,
                                                  account.email,
                                                  account.role)

    def remove_account(self, username):
        """Remove an account."""

        if username == 'root':
            raise ValueError("Cannot removed root account")

        account = Session().query(TblAccount) \
                           .filter(TblAccount.username == str(username)) \
                           .first()
        if not account:
            raise KeyError(username)

        session = Session()
        session.delete(account)
        session.commit()

        del self.accounts[username]
        to_be_deleted = [x.tenant_id for x in self.tenants.values()
                         if x.owner == username]

        for tenant_id in to_be_deleted:
            self.remove_tenant(tenant_id)

    def register_app(self, name, init_method, params):
        """Register new app."""

        tenant_id = params['tenant_id']

        if tenant_id not in self.tenants:
            self.log.error("Invalid tenant: %s", tenant_id)
            return

        if name in self.tenants[tenant_id].components:
            self.log.error("'%s' already registered", name)
            raise ValueError("%s already registered" % name)

        self.log.info("Registering '%s'", name)

        self.tenants[tenant_id].components[name] = init_method(**params)

        if hasattr(self.tenants[tenant_id].components[name], "start"):
            self.tenants[tenant_id].components[name].start()

    def register(self, name, init_method, params):
        """Register new component."""

        if name in self.components:
            self.log.error("'%s' already registered", name)
            raise ValueError("%s already registered" % name)

        self.log.info("Registering '%s'", name)

        self.components[name] = init_method(**params)

        if hasattr(self.components[name], "start"):
            self.components[name].start()

    def unregister_app(self, tenant_id, app_id):
        """Unregister app."""

        tenant = self.tenants[tenant_id]

        if app_id not in tenant.components:
            self.log.error("'%s' not registered", app_id)
            raise ValueError("%s not registered" % app_id)

        self.log.info("Unregistering: %s (%s)", app_id, tenant_id)

        app = tenant.components[app_id]

        from empower.core.app import EmpowerApp

        if not issubclass(type(app), EmpowerApp):
            raise ValueError("Module %s cannot be removed" % app_id)

        app.stop()

        del tenant.components[app_id]

    def unregister(self, name):
        """Unregister module."""

        self.log.info("Unregistering '%s'", name)

        worker = self.components[name]

        from empower.core.module import ModuleWorker

        if not issubclass(type(worker), ModuleWorker):
            raise ValueError("Module %s cannot be removed" % name)

        for module_id in list(self.components[name].modules.keys()):
            self.components[name].remove_module(module_id)

        del self.components[name]

    def get_account(self, username):
        """Load user credential from the username."""

        if username not in self.accounts:
            return None

        return self.accounts[username]

    def check_permission(self, username, password):
        """Check if username/password match."""

        if username not in self.accounts:
            return False

        if self.accounts[username].password != password:
            return False

        return True

    def add_tenant(self, owner, desc, tenant_name, bssid_type,
                   tenant_id=None, plmn_id=None):

        """Create new Tenant."""

        if tenant_id in self.tenants:
            raise ValueError("Tenant %s exists" % tenant_id)

        plmn_ids = [tenant.plmn_id for tenant in self.tenants.values()]

        if plmn_id and plmn_id in plmn_ids:
            raise ValueError("PLMN ID %s exists" % plmn_id)

        if bssid_type not in T_TYPES:
            raise ValueError("Invalid bssid_type %s" % bssid_type)

        session = Session()

        if tenant_id:
            request = TblTenant(tenant_id=tenant_id,
                                tenant_name=tenant_name,
                                owner=owner,
                                desc=desc,
                                bssid_type=bssid_type,
                                plmn_id=plmn_id)
        else:
            request = TblTenant(owner=owner,
                                tenant_name=tenant_name,
                                desc=desc,
                                bssid_type=bssid_type,
                                plmn_id=plmn_id)

        session.add(request)
        session.commit()

        self.tenants[request.tenant_id] = \
            Tenant(request.tenant_id,
                   request.tenant_name,
                   self.accounts[owner].username,
                   desc,
                   request.bssid_type,
                   request.plmn_id)

        # create default queue
        dscp = DSCP()
        descriptor = {}

        self.tenants[request.tenant_id].add_slice(dscp, descriptor)

        return request.tenant_id

    def remove_tenant(self, tenant_id):
        """Delete existing Tenant."""

        if tenant_id not in self.tenants:
            raise KeyError(tenant_id)

        tenant = self.tenants[tenant_id]

        # remove slices in this tenant
        for dscp in list(tenant.slices):
            tenant.del_slice(dscp)

        # remove lvaps in this tenant
        for lvap_addr in list(tenant.lvaps):
            self.remove_lvap(lvap_addr)

        # remove tenant
        del self.tenants[tenant_id]

        tenant = Session().query(TblTenant) \
                          .filter(TblTenant.tenant_id == tenant_id) \
                          .first()

        session = Session()
        session.delete(tenant)
        session.commit()

        # remove running modules
        for component in self.components.values():

            if not hasattr(component, 'modules'):
                continue

            to_be_removed = []

            for module in component.modules.values():
                if module.tenant_id == tenant_id:
                    to_be_removed.append(module.module_id)

            for module_id in to_be_removed:
                component.remove_module(module_id)

    def load_tenant(self, tenant_name):
        """Load tenant from network name (SSID)."""

        for tenant in self.tenants.values():
            if tenant.tenant_name == tenant_name:
                return tenant

        return None

    def load_tenant_by_plmn_id(self, plmn_id):
        """Load tenant from network name."""

        for tenant in self.tenants.values():
            if tenant.plmn_id == plmn_id:
                return tenant

        return None

    def remove_lvap(self, lvap_addr):
        """Remove LVAP from the network"""

        if lvap_addr not in self.lvaps:
            return

        lvap = self.lvaps[lvap_addr]

        if lvap.tenant:

            # removing LVAP from tenant, need first to look for right tenant
            if lvap.addr in lvap.tenant.lvaps:
                self.log.info("Removing %s from tenant %s", lvap.addr,
                              lvap.ssid)
                del lvap.tenant.lvaps[lvap.addr]

            # Raise LVAP leave event
            from empower.lvapp.lvappserver import LVAPPServer
            lvapp_server = self.components[LVAPPServer.__module__]
            lvapp_server.send_lvap_leave_message_to_self(lvap)

        # Reset LVAP
        self.log.info("Deleting LVAP (DL+UL): %s", lvap.addr)
        lvap.clear_blocks()

        del self.lvaps[lvap.addr]

    def remove_ue(self, ue_id):
        """Remove UE from the network"""

        if ue_id not in self.ues:
            return

        ue = self.ues[ue_id]

        if ue.tenant:

            # removing UE from tenant, need first to look for right tenant
            if ue.ue_id in ue.tenant.ues:
                self.log.info("Removing %s from tenant %s", ue.ue_id,
                              ue.tenant.plmn_id)
                del ue.tenant.ues[ue.ue_id]

            # Raise UE leave event
            from empower.vbsp.vbspserver import VBSPServer
            vbsp_server = self.components[VBSPServer.__module__]
            vbsp_server.send_ue_leave_message_to_self(ue)

        del self.ues[ue.ue_id]

    def find_ue_by_rnti(self, rnti, pci, vbs):
        """Find a UE using the tuple rnti, pci, vbs."""

        for ue in self.ues.values():

            if ue.rnti == rnti and \
               ue.cell.pci == pci and \
               ue.cell.vbs == vbs:

                return ue

        return None

    def assoc_id(self):
        """Generate new assoc id."""

        assoc_id = randint(1, 2007)

        return assoc_id
