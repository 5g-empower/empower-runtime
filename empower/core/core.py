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
from empower.persistence import Session
from empower.persistence.persistence import TblTenant
from empower.persistence.persistence import TblAccount
from empower.persistence.persistence import TblBelongs
from empower.persistence.persistence import TblPendingTenant
from empower.core.account import Account
from empower.core.tenant import Tenant
from empower.core.acl import ACL
from empower.persistence.persistence import TblAllow
from empower.persistence.persistence import TblDeny
from empower.persistence.persistence import TblIMSI2MAC

import empower.logger
LOG = empower.logger.get_logger()

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

        LOG.info("Generating default accounts")

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


class EmpowerRuntime(object):
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
        self.feeds = {}
        self.allowed = {}
        self.denied = {}
        self.imsi2mac = {}

        LOG.info("Starting EmPOWER Runtime")

        # generate default users if database is empty
        generate_default_accounts()

        # load defaults
        LOG.info("Loading EmPOWER Runtime defaults")
        self.__load_accounts()
        self.__load_tenants()
        self.__load_acl()
        self.__load_imsi2mac()

        if options.ctrl_adv:
            self.__ifname = options.ctrl_adv_iface
            self.__ctrl_ip = options.ctrl_ip
            self.__ctrl_port = options.ctrl_port
            self.__start_adv()

    def __start_adv(self):
        """Star ctrl advertising."""

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        info = fcntl.ioctl(sock.fileno(), 0x8927, struct.pack('256s',
                           self.__ifname[:15].encode('utf-8')))

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

    def __load_imsi2mac(self):
        """Load IMSI to MAC mapped values."""

        for entry in Session().query(TblIMSI2MAC).all():
            self.imsi2mac[entry.imsi] = entry.addr

    def add_imsi2mac(self, imsi, addr):
        """Add IMSI to MAC mapped value to table."""

        imsi2mac = Session().query(TblIMSI2MAC) \
                         .filter(TblIMSI2MAC.imsi == imsi) \
                         .first()
        if imsi2mac:
            raise ValueError(imsi)

        try:

            session = Session()

            session.add(TblIMSI2MAC(imsi=imsi, addr=addr))
            session.commit()

        except IntegrityError:
            session.rollback()
            raise ValueError("MAC address must be unique %s", addr)

        self.imsi2mac[imsi] = addr

    def remove_imsi2mac(self, imsi):
        """Remove IMSI to MAC mapped value from table."""

        imsi2mac = Session().query(TblIMSI2MAC) \
                         .filter(TblIMSI2MAC.imsi == imsi) \
                         .first()
        if not imsi2mac:
            raise KeyError(imsi)

        session = Session()
        session.delete(imsi2mac)
        session.commit()

        del self.imsi2mac[imsi]

    def __load_acl(self):
        """ Load ACL list. """

        for allow in Session().query(TblAllow).all():

            if allow.addr in self.allowed:
                raise ValueError(allow.addr_str)

            acl = ACL(allow.addr, allow.label)
            self.allowed[allow.addr] = acl

        for deny in Session().query(TblDeny).all():
            if deny.addr in self.denied:
                raise ValueError(deny.addr_str)

            acl = ACL(deny.addr, deny.label)
            self.denied[deny.addr] = acl

    def add_allowed(self, sta_addr, label):
        """ Add entry to ACL. """

        allow = Session().query(TblAllow) \
                         .filter(TblAllow.addr == sta_addr) \
                         .first()
        if allow:
            raise ValueError(sta_addr)

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
            raise KeyError(sta_addr)

        session = Session()
        session.delete(allow)
        session.commit()

        del self.allowed[sta_addr]

    def add_denied(self, sta_addr, label):
        """ Add entry to ACL. """

        deny = Session().query(TblDeny) \
                        .filter(TblDeny.addr == sta_addr) \
                        .first()
        if deny:
            raise ValueError(sta_addr)

        session = Session()
        session.add(TblDeny(addr=sta_addr, label=label))
        session.commit()

        acl = ACL(sta_addr, label)
        self.denied[sta_addr] = acl

        return acl

    def remove_denied(self, sta_addr):
        """ Remove entry from ACL. """

        deny = Session().query(TblDeny) \
                        .filter(TblDeny.addr == sta_addr) \
                        .first()
        if not deny:
            raise KeyError(sta_addr)

        session = Session()
        session.delete(deny)
        session.commit()

        del self.denied[sta_addr]

    def is_allowed(self, src):
        """ Check if station is allowed. """

        return (self.allowed and src in self.allowed) or not self.allowed

    def is_denied(self, src):
        """ Check if station is denied. """

        return self.denied and src in self.denied

    def create_account(self, username, password, role, name, surname, email):
        """Create a new account."""

        if username in self.accounts:
            LOG.error("'%s' already registered", username)
            raise ValueError("%s already registered" % username)

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

    def update_account(self, username, request):
        """Update an account."""

        account = self.accounts[username]

        for param in request:
            setattr(account, param, request[param])

    def register_app(self, name, init_method, params):
        """Register new component."""

        tenant_id = params['tenant_id']

        if tenant_id not in self.tenants:
            return

        if name in self.tenants[tenant_id].components:
            LOG.error("'%s' already registered", name)
            raise ValueError("%s already registered" % name)

        LOG.info("Registering '%s'", name)

        self.tenants[tenant_id].components[name] = init_method(**params)

        if hasattr(self.tenants[tenant_id].components[name], "start"):
            self.tenants[tenant_id].components[name].start()

    def register(self, name, init_method, params):
        """Register new component."""

        if name in self.components:
            LOG.error("'%s' already registered", name)
            raise ValueError("%s already registered" % name)

        LOG.info("Registering '%s'", name)

        self.components[name] = init_method(**params)

        if hasattr(self.components[name], "start"):
            self.components[name].start()

    def unregister_app(self, tenant_id, app_id):
        """Unregister component."""

        LOG.info("Unregistering: %s (%s)", app_id, tenant_id)

        tenant = self.tenants[tenant_id]
        app = tenant.components[app_id]

        from empower.core.app import EmpowerApp

        if not issubclass(type(app), EmpowerApp):
            raise ValueError("Module %s cannot be removed", app_id)

        app.stop()
        del tenant.components[app_id]

    def unregister(self, name):
        """Unregister component."""

        LOG.info("Unregistering '%s'", name)

        worker = self.components[name]

        from empower.core.module import ModuleWorker

        if not issubclass(type(worker), ModuleWorker):
            raise ValueError("Module %s cannot be removed", name)

        to_be_removed = []

        for module in self.components[name].modules.values():
            to_be_removed.append(module.module_id)

        for remove in to_be_removed:
            self.components[name].remove_module(remove)

        self.components[name].remove_handlers()
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
            raise ValueError("Tenant %s exists", tenant_id)

        try:

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

        except IntegrityError:
            session.rollback()
            raise ValueError("Tenant name %s exists", tenant_name)

        self.tenants[request.tenant_id] = \
            Tenant(request.tenant_id,
                   request.tenant_name,
                   self.accounts[owner].username,
                   desc,
                   request.bssid_type,
                   request.plmn_id)

        return request.tenant_id

    @classmethod
    def load_pending_tenant(cls, tenant_id):
        """Load pending tenant request."""

        return Session().query(TblPendingTenant) \
                        .filter(TblPendingTenant.tenant_id == tenant_id) \
                        .first()

    @classmethod
    def load_pending_tenants(cls, username=None):
        """Fetch pending tenants requests."""

        if username:
            return Session().query(TblPendingTenant) \
                            .filter(TblPendingTenant.owner == username) \
                            .all()
        else:
            return Session().query(TblPendingTenant).all()

    def request_tenant(self, owner, desc, tenant_name, bssid_type,
                       tenant_id=None, plmn_id=None):

        """Request new Tenant."""

        if tenant_id in self.tenants:
            raise ValueError("Tenant %s exists", tenant_id)

        if self.load_pending_tenant(tenant_id):
            raise ValueError("Tenant %s exists", tenant_id)

        try:

            session = Session()

            if tenant_id:
                request = TblPendingTenant(tenant_id=tenant_id,
                                           owner=owner,
                                           tenant_name=tenant_name,
                                           desc=desc,
                                           bssid_type=bssid_type,
                                           plmn_id=plmn_id)
            else:
                request = TblPendingTenant(owner=owner,
                                           tenant_name=tenant_name,
                                           desc=desc,
                                           bssid_type=bssid_type,
                                           plmn_id=plmn_id)

            session.add(request)
            session.commit()

        except IntegrityError:
            session.rollback()
            raise ValueError("Tenant name %s exists", tenant_name)

        return request.tenant_id

    @classmethod
    def reject_tenant(cls, tenant_id):
        """Reject previously requested Tenant."""

        pending = Session().query(TblPendingTenant) \
            .filter(TblPendingTenant.tenant_id == tenant_id) \
            .first()

        if not pending:
            raise KeyError(tenant_id)

        session = Session()
        session.delete(pending)
        session.commit()

    def remove_tenant(self, tenant_id):
        """Delete existing Tenant."""

        if tenant_id not in self.tenants:
            raise KeyError(tenant_id)

        tenant = self.tenants[tenant_id]

        # remove pnfdev in this tenant
        devs = Session().query(TblBelongs) \
                        .filter(TblBelongs.tenant_id == tenant_id)

        for dev in devs:
            session = Session()
            session.delete(dev)
            session.commit()

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
        """Load tenant from network name."""

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
                LOG.info("Removing %s from tenant %s", lvap.addr, lvap.ssid)
                del lvap.tenant.lvaps[lvap.addr]

            # Raise LVAP leave event
            from empower.lvapp.lvappserver import LVAPPServer
            lvapp_server = self.components[LVAPPServer.__module__]
            lvapp_server.send_lvap_leave_message_to_self(lvap)

        # Reset LVAP
        LOG.info("Deleting LVAP (DL+UL): %s", lvap.addr)
        lvap.clear_downlink()
        lvap.clear_uplink()

        del self.lvaps[lvap.addr]

    def remove_lvap(self, lvap_addr):
        """Remove LVAP from the network"""

        if lvap_addr not in self.lvaps:
            return

        lvap = self.lvaps[lvap_addr]

        if lvap.tenant:

            # removing LVAP from tenant, need first to look for right tenant
            if lvap.addr in lvap.tenant.lvaps:
                LOG.info("Removing %s from tenant %s", lvap.addr, lvap.ssid)
                del lvap.tenant.lvaps[lvap.addr]

            # Raise LVAP leave event
            from empower.lvapp.lvappserver import LVAPPServer
            lvapp_server = self.components[LVAPPServer.__module__]
            lvapp_server.send_lvap_leave_message_to_self(lvap)

        # Reset LVAP
        LOG.info("Deleting LVAP (DL+UL): %s", lvap.addr)
        lvap.clear_downlink()
        lvap.clear_uplink()

        del self.lvaps[lvap.addr]

    def remove_ue(self, ue_addr):
        """Remove UE from the network"""

        if ue_addr not in self.ues:
            return

        ue = self.ues[ue_addr]

        if ue.tenant:

            # removing UE from tenant, need first to look for right tenant
            if ue.addr in ue.tenant.ues:
                LOG.info("Removing %s from tenant %u", ue.addr, ue.plmn_id)
                del ue.tenant.ues[ue.addr]

            # Raise UE leave event
            from empower.vbsp.vbspserver import VBSPServer
            vbsp_server = self.components[VBSPServer.__module__]
            vbsp_server.send_ue_leave_message_to_self(ue)

        del self.ues[ue.addr]
