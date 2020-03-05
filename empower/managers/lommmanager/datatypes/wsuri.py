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
"""Web Socket URI"""

import ipaddress
import re

from pymodm.errors import ValidationError
from pymodm.base.fields import MongoBaseField
from pymodm import validators
# from pymodm.compat import PY3


class WSURIField(MongoBaseField):
    """A field that stores WS URIs.

    This field only accepts 'ws', 'wss's.
    """
    SCHEMES = set(['ws', 'wss'])
    DOMAIN_PATTERN = re.compile(
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2, 6}\.?|[A-Z0-9-]{2,}(?<!-)\.?)'  # domain
        r'(?::\d+)?\Z',  # optional port
        re.IGNORECASE
    )
    PATH_PATTERN = re.compile(r'\A\S*\Z')

    def __init__(self, verbose_name=None, mongo_name=None, **kwargs):
        """
        :parameters:
          - `verbose_name`: A human-readable name for the Field.
          - `mongo_name`: The name of this field when stored in MongoDB.

        .. seealso:: constructor for
                     :class:`~pymodm.base.fields.MongoBaseField`
        """
        super(WSURIField, self).__init__(verbose_name=verbose_name,
                                         mongo_name=mongo_name,
                                         **kwargs)

        def validate_url(url):
            scheme, rest = url.split('://')
            if scheme.lower() not in self.SCHEMES:
                raise ValidationError('Unrecognized scheme: ' + scheme)
            domain, _, path = rest.partition('/')
            if not re.match(self.PATH_PATTERN, path):
                raise ValidationError('Invalid path: ' + path)
            if not re.match(self.DOMAIN_PATTERN, domain):
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
            validators.append(validate_url)
