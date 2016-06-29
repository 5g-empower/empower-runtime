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

"""Virtual port."""

import json
import http.client

from uuid import UUID

from urllib.parse import urlparse
from empower.core.jsonserializer import EmpowerEncoder

import empower.logger
LOG = empower.logger.get_logger()


def key_to_match(key):
    """Convert a OF match in dictionary form to a string."""

    match = ";".join(["%s=%s" % x for x in sorted(key.items())])
    return match


def match_to_key(match):
    """Convert a OF match string in dictionary form"""

    key = {}

    for token in match.split(";"):
        key_t, value_t = token.split("=")
        key[key_t] = value_t

    return key


def add_intent(intent):
    """Create new intent."""

    key = match_to_key(intent['match'])

    if 'dpid' in key:
        del key['dpid']

    if 'port_id' in key:
        del key['port_id']

    if key:
        intent['match'] = key
    else:
        del intent['match']

    body = json.dumps(intent, indent=4, cls=EmpowerEncoder)

    LOG.info("POST: %s\n%s", "/intent/rules", body)

    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
    }

    try:

        conn = http.client.HTTPConnection("localhost", 8080)
        conn.request("POST", "/intent/rules", body, headers)
        response = conn.getresponse()
        conn.close()

        ret = (response.status, response.reason, response.read())

        if ret[0] == 201:

            location = response.getheader("Location", None)
            url = urlparse(location)
            uuid = UUID(url.path.split("/")[-1])

            LOG.info("Result: %u %s (%s)", ret[0], ret[1], uuid)

            return uuid

        LOG.info("Result: %u %s", ret[0], ret[1])

    except ConnectionRefusedError:

        LOG.error("Intent interface not found")

    return None


def del_intent(uuid):
    """Remove intent."""

    if not uuid:
        LOG.warning("UUID not specified")
        return

    LOG.info("DELETE: %s", uuid)

    try:

        conn = http.client.HTTPConnection("localhost", 8080)
        conn.request("DELETE", "/intent/rules/%s" % uuid)
        response = conn.getresponse()

        ret = (response.status, response.reason, response.read())

        LOG.info("Result: %u %s", ret[0], ret[1])
        conn.close()

    except ConnectionRefusedError:

        LOG.error("Intent interface not found")
