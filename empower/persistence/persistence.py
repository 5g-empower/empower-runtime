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

"""Empower persistence layer."""

import uuid
import empower.datatypes.etheraddress as etheraddress
import empower.datatypes.ssid as ssid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.types import TypeDecorator, Unicode

from empower.persistence import ENGINE

Base = declarative_base()


class UUID(TypeDecorator):
    """UUID type."""

    impl = Unicode

    def __init__(self):
        self.impl.length = 36
        TypeDecorator.__init__(self, length=self.impl.length)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, uuid.UUID):
            return str(value)
        elif value and not isinstance(value, uuid.UUID):
            raise ValueError('value %s is not a valid uuid.UUID' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return uuid.UUID(value)
        else:
            return None

    def is_mutable(self):
        return False


class EtherAddress(TypeDecorator):
    """EtherAddress type."""

    impl = Unicode

    def __init__(self):
        self.impl.length = 6
        TypeDecorator.__init__(self, length=self.impl.length)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, etheraddress.EtherAddress):
            return value.to_str()
        elif value and not isinstance(value, etheraddress.EtherAddress):
            raise ValueError('value %s is not a valid EtherAddress' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return etheraddress.EtherAddress(value)
        else:
            return None

    def is_mutable(self):
        return False


class SSID(TypeDecorator):
    """EtherAddress type."""

    impl = Unicode

    def __init__(self):
        self.impl.length = 30
        TypeDecorator.__init__(self, length=self.impl.length)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, ssid.SSID):
            return value.to_str()
        elif value and not isinstance(value, ssid.SSID):
            raise ValueError('value %s is not a valid SSID' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return ssid.SSID(value)
        else:
            return None

    def is_mutable(self):
        return False


class TblFeed(Base):
    """ Energino Feeds Table. """

    __tablename__ = 'Feed'

    feed_id = Column(Integer, primary_key=True)
    title = Column(String)
    created = Column(String)
    updated = Column(String)
    addr = Column("addr", EtherAddress(), nullable=True)


class TblAccount(Base):
    """ Account table. """

    __tablename__ = 'account'

    username = Column(String, primary_key=True)
    password = Column(String)
    name = Column(String)
    surname = Column(String)
    email = Column(String)
    role = Column(String)


class TblPendingTenant(Base):
    """ List of pending Tenant request. """

    __tablename__ = 'pending_tenant'

    tenant_id = Column("tenant_id",
                       UUID(),
                       primary_key=True,
                       default=uuid.uuid4)
    plmn_id = Column("plmn_id",
                     Integer,
                     default=True)
    tenant_name = Column(SSID, unique=True)
    desc = Column(String)
    owner = Column(String)
    bssid_type = Column(String)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the request """

        return {'tenant_id': self.tenant_id,
                'owner': self.owner,
                'plmn_id': self.plmn_id,
                'tenant_name': self.tenant_name,
                'desc': self.desc,
                'bssid_type': self.bssid_type}


class TblTenant(Base):
    """ Tenant table. """

    __tablename__ = 'tenant'

    tenant_id = Column("tenant_id",
                       UUID(),
                       primary_key=True,
                       default=uuid.uuid4)
    plmn_id = Column("plmn_id",
                     Integer,
                     default=True)
    tenant_name = Column(SSID, unique=True)
    desc = Column(String)
    owner = Column(String)
    bssid_type = Column(String)


class TblPNFDev(Base):
    """ Programmable network fabric device table. """

    __tablename__ = 'pnfdev'

    addr = Column("addr",
                  EtherAddress(),
                  primary_key=True)
    label = Column(String)

    tbl_type = Column(String(20))

    __mapper_args__ = {
        'polymorphic_on': tbl_type,
        'polymorphic_identity': 'pnfdevs'
    }


class TblBelongs(Base):
    """Link PNFDevs with Tenants"""

    __tablename__ = 'belongs'

    addr = Column(EtherAddress(),
                  ForeignKey('pnfdev.addr'),
                  primary_key=True)

    tenant_id = Column(UUID(),
                       ForeignKey('tenant.tenant_id'),
                       primary_key=True)


class TblCPP(TblPNFDev):
    """ Programmable network fabric device table. """

    __mapper_args__ = {
        'polymorphic_identity': 'cpps'
    }


class TblWTP(TblPNFDev):
    """ Wireless Termination point. """

    __mapper_args__ = {
        'polymorphic_identity': 'wtps'
    }


class TblVBS(TblPNFDev):
    """ Virtual Base Station Point. """

    __mapper_args__ = {
        'polymorphic_identity': 'vbses'
    }


class TblAllow(Base):
    """ Allow table. """

    __tablename__ = 'allow'

    addr = Column("addr",
                  EtherAddress(),
                  primary_key=True)

    label = Column(String)


class TblDeny(Base):
    """ Deny table. """

    __tablename__ = 'deny'

    addr = Column("addr",
                  EtherAddress(),
                  primary_key=True)

    label = Column(String)


class TblIMSI2MAC(Base):
    """ IMSI to MAC address mapping table. """

    __tablename__ = 'imsi2mac'

    imsi = Column("imsi",
                  Integer,
                  primary_key=True)

    addr = Column("addr",
                  EtherAddress(),
                  unique=True)

Base.metadata.create_all(ENGINE)
