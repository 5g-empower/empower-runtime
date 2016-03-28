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

    intent['match'] = key

    body = json.dumps(intent, indent=4, cls=EmpowerEncoder)

    LOG.info("POST: %s\n%s", "/empower/vnfrule/", body)

    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
    }

    try:

        conn = http.client.HTTPConnection("localhost", 8080)
        conn.request("POST", "/empower/vnfrule/", body, headers)
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
        conn.request("DELETE", "/empower/vnfrule/%s" % uuid)
        response = conn.getresponse()

        ret = (response.status, response.reason, response.read())

        LOG.info("Result: %u %s", ret[0], ret[1])
        conn.close()

    except ConnectionRefusedError:

        LOG.error("Intent interface not found")
