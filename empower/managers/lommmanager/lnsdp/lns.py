#!/usr/bin/env python3
#
# Copyright (c) 2020 Fondazione Bruno Kessler
# Author(s): Cristina Costa (ccosta@fbk.eu)
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

"""Base device class."""

import logging
import ipaddress
import re

from datetime import datetime

from pymodm import MongoModel, fields
from pymodm.errors import ValidationError

from empower.core.eui64 import EUI64Field
from empower.core.serialize import serializable_dict


def validator_ws_uri(value):
    """Validate if the value is a valid ws/wss uri."""
    DOMAIN_PATTERN = re.compile(
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2, 6}\.?|[A-Z0-9-]{2,}(?<!-)\.?)'  # domain
        r'(?::\d+)?\Z',  # optional port
        re.IGNORECASE
    )
    PATH_PATTERN = re.compile(r'\A\S*\Z')

    scheme, rest = value.split('://')

    if scheme.lower() not in ['ws', 'wss']:
        raise ValidationError('Unrecognized scheme: ' + scheme)

    domain, _, path = rest.partition('/')

    if not PATH_PATTERN.match(path):
        raise ValidationError('Invalid path: ' + path)

    if not DOMAIN_PATTERN.match(domain):
        # Check if it is an IP address
        try:
            ipaddress.ip_address(domain)
        except ValueError:
            try:
                # Check if there's a port. Remove it, and try again.
                domain, port = domain.rsplit(':', 1)
                ipaddress.ip_address(domain)
            except ValueError:
                raise ValidationError('Invalid URL: ' + rest)


@serializable_dict
class LNS(MongoModel):
    """LNS class.

    Attributes:
        euid: This LNS EUID
        ip:   This LNS IP address (IPAddress)
        port: This LNS port
        desc: A human-radable description of this Device (str)
        log:  logging facility
    """

    euid = EUI64Field(primary_key=True)  # 64 bit lns identifier, EUI-64
    uri = fields.CharField(required=True,
                           validators=[validator_ws_uri])
    lgtws = fields.ListField(required=False, blank=True,
                             field=EUI64Field(),
                             verbose_name="List of lGtws",
                             mongo_name="lgtws"
                             )
    desc = fields.CharField(required=False)

    class Meta:
        """Specify custom collection name in mongodb."""

        collection_name = "lomm_lns"

    def __init__(self, **kwargs):
        """Initialize attributes."""
        super().__init__(**kwargs)

        self.last_seen = 0
        self.last_seen_ts = 0
        self.period = 0
        self.log = logging.getLogger("%s" % self.__class__.__module__)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""
        date = datetime.fromtimestamp(self.last_seen_ts) \
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        out = {
            'euid': self.euid,
            'desc': self.desc,
            'uri': self.uri,
            'lgtws': [lgtw for lgtw in self.lgtws],
            'last_seen': self.last_seen,
            'last_seen_ts': date,
            'period': self.period,
        }

        return out

    def to_str(self):
        """Return an ASCII representation of the object."""
        return "LNSS object \"%s\", euid=%s" % (self.desc, self.euid.id6)

    def __str__(self):
        """Return string format."""
        return self.to_str()

    def __hash__(self):
        """Return hash."""
        return hash(self.euid)

    def __eq__(self, other):
        """Return if are equal based on euid."""
        if isinstance(other, LNS):
            return self.euid == other.euid
        return False

    def __ne__(self, other):
        """Return negation."""
        return not self.__eq__(other)

    def __repr__(self):
        """Return represention."""
        return self.__class__.__name__ + "('" + self.to_str() + "')"
