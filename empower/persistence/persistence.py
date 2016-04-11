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
        self.impl.length = 16
        TypeDecorator.__init__(self, length=self.impl.length)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, uuid.UUID):
            return value.bytes
        elif value and not isinstance(value, uuid.UUID):
            raise ValueError('value %s is not a valid uuid.UUID' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return uuid.UUID(bytes=value)
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
            return value.to_raw()
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
            return value.to_raw()
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
    pnfdev_addr = Column(EtherAddress, nullable=True)


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
    tenant_name = Column(SSID, unique=True)
    desc = Column(String)
    owner = Column(String)
    bssid_type = Column(String)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the request """

        return {'tenant_id': self.tenant_id,
                'owner': self.owner,
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


class TblOAIN(TblPNFDev):
    """ OAI Node. """

    __mapper_args__ = {
        'polymorphic_identity': 'oains'
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


Base.metadata.create_all(ENGINE)
