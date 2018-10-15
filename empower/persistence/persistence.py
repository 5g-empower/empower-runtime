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

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.types import TypeDecorator, Unicode

import empower.datatypes.etheraddress as etheraddress
import empower.datatypes.ssid as ssid
import empower.datatypes.plmnid as plmnid
import empower.datatypes.dscp as dscp
import empower.datatypes.match as match

from empower.persistence import ENGINE

Base = declarative_base()


class UUID(TypeDecorator):
    """UUID type."""

    impl = Unicode

    def __init__(self):
        super().__init__(length=36)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, uuid.UUID):
            return str(value)

        if value and not isinstance(value, uuid.UUID):
            raise ValueError('value %s is not a valid uuid.UUID' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return uuid.UUID(value)

        return None

    @classmethod
    def is_mutable(cls):
        """Object is not mutable."""

        return False


class EtherAddress(TypeDecorator):
    """EtherAddress type."""

    impl = Unicode

    def __init__(self):
        super().__init__(length=6)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, etheraddress.EtherAddress):
            return value.to_str()

        if value and not isinstance(value, etheraddress.EtherAddress):
            raise ValueError('value %s is not a valid EtherAddress' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return etheraddress.EtherAddress(value)

        return None

    @classmethod
    def is_mutable(cls):
        """Object is not mutable."""

        return False


class SSID(TypeDecorator):
    """EtherAddress type."""

    impl = Unicode

    def __init__(self):
        super().__init__(length=30)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, ssid.SSID):
            return value.to_str()

        if value and not isinstance(value, ssid.SSID):
            raise ValueError('value %s is not a valid SSID' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return ssid.SSID(value)

        return None

    @classmethod
    def is_mutable(cls):
        """Object is not mutable."""

        return False


class PLMNID(TypeDecorator):
    """PLMNID type."""

    impl = Unicode

    def __init__(self):
        super().__init__(length=5)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, plmnid.PLMNID):
            return value.to_str()

        if value and not isinstance(value, plmnid.PLMNID):
            raise ValueError('value %s is not a valid PLMNID' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return plmnid.PLMNID(value)

        return None

    @classmethod
    def is_mutable(cls):
        """Object is not mutable."""

        return False


class DSCP(TypeDecorator):
    """DSCP type."""

    impl = Unicode

    def __init__(self):
        super().__init__(length=2)

    def process_bind_param(self, value, dialect=None):

        if isinstance(value, dscp.DSCP):
            return value.to_str()

        raise ValueError('value %s is not a valid DSCP' % value)

    def process_result_value(self, value, dialect=None):

        if value:
            return dscp.DSCP(value)

        return None

    @classmethod
    def is_mutable(cls):
        """Object is not mutable."""

        return False


class Match(TypeDecorator):
    """Match type adapter."""

    impl = Unicode

    def __init__(self):
        super().__init__(length=100)

    def process_bind_param(self, value, dialect=None):

        if value and isinstance(value, match.Match):
            return value.to_str()
        elif value and not isinstance(value, match.Match):
            raise ValueError('value %s is not a valid Match' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):

        if value:
            return match.Match(value)

        return None

    @classmethod
    def is_mutable(cls):
        """Object is not mutable."""

        return False


class TblAccount(Base):
    """ Account table. """

    __tablename__ = 'account'

    username = Column(String, primary_key=True)
    password = Column(String)
    name = Column(String)
    surname = Column(String)
    email = Column(String)
    role = Column(String)


class TblTenant(Base):
    """ Tenant table. """

    __tablename__ = 'tenant'

    tenant_id = Column("tenant_id",
                       UUID(),
                       primary_key=True,
                       default=uuid.uuid4)
    plmn_id = Column("plmn_id", PLMNID, unique=True)
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


class TblSwitch(TblPNFDev):
    """ OpenFlow Switch. """

    __mapper_args__ = {
        'polymorphic_identity': 'switches'
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


class TblSlice(Base):
    """ Slice table. """

    __tablename__ = 'slice'

    dscp = Column("dscp", DSCP(), primary_key=True)

    tenant_id = Column(UUID(),
                       ForeignKey('tenant.tenant_id'),
                       primary_key=True)

    wifi = Column(String)

    lte = Column(String)


class TblSliceBelongs(Base):
    """Link PNFDevs with Tenants"""

    __tablename__ = 'slice_belongs'

    dscp = Column(DSCP(),
                  primary_key=True)

    addr = Column(EtherAddress(),
                  ForeignKey('pnfdev.addr'),
                  primary_key=True)

    tenant_id = Column(UUID(),
                       ForeignKey('tenant.tenant_id'),
                       primary_key=True)

    properties = Column(String)


class TblTrafficRule(Base):
    """ Traffic Rule Queue table. """

    __tablename__ = 'traffic_rule'

    match = Column("match", Match(), primary_key=True)

    tenant_id = Column(UUID(),
                       ForeignKey('tenant.tenant_id'),
                       primary_key=True,)

    dscp = Column(DSCP())

    label = Column(String)

    priority = Column(String)


Base.metadata.create_all(ENGINE)
