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

"""Intent server module."""

import tornado
import json
import http.client

from uuid import UUID
from urllib.parse import urlparse

from empower.core.jsonserializer import EmpowerEncoder

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

DEFAULT_PORT = 4444


class IntentHandler(tornado.web.RequestHandler):
    """Datastreams handler."""

    HANDLERS = [r"/intents/([a-zA-Z0-9-]*)"]


class IntentServer(tornado.web.Application):
    """Intent Server."""

    handlers = [IntentHandler]

    def __init__(self, port):

        self.port = int(port)
        self.intent_host = "localhost"
        self.intent_port = 8080
        self.intent_url = "/intent/rules"

        handlers = []
        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler))

        tornado.web.Application.__init__(self, handlers)
        http_server = tornado.httpserver.HTTPServer(self)
        http_server.listen(self.port)

        self.get_intent()
        self.remove_intent()

    def get_intent(self, uuid=None):
        """Remove intent."""

        if uuid:
            LOG.info("Fetching intent: %s", uuid)
        else:
            LOG.info("Fetching intent: ALL")

        try:

            conn = \
                http.client.HTTPConnection(self.intent_host, self.intent_port)

            if uuid:
                conn.request("GET", self.intent_url + "/%s" % uuid)
            else:
                conn.request("GET", self.intent_url)

            response = conn.getresponse()

            ret = (response.status, response.reason, response.read())

            LOG.info("Result: %u %s", ret[0], ret[1])
            conn.close()

        except ConnectionRefusedError:
            LOG.error("Intent interface not found")

        except Exception as ex:
            LOG.exception(ex)

    def send_intent(self, intent):
        """Create new intent."""

        body = json.dumps(intent, indent=4, cls=EmpowerEncoder)

        LOG.info("Creating intent:\n%s", body)

        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }

        try:

            conn = \
                http.client.HTTPConnection(self.intent_host, self.intent_port)

            conn.request("POST", self.intent_url, body, headers)
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

        except Exception as ex:
            LOG.exception(ex)

        return None

    def update_intent(self, uuid, intent):
        """Create new intent."""

        body = json.dumps(intent, indent=4, cls=EmpowerEncoder)

        LOG.info("Updating intent: %s\n%s", uuid, body)

        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }

        try:

            conn = \
                http.client.HTTPConnection(self.intent_host, self.intent_port)

            conn.request("PUT", self.intent_url + "/%s" % uuid, body, headers)
            response = conn.getresponse()
            conn.close()

            ret = (response.status, response.reason, response.read())

            if ret[0] == 204:
                LOG.info("Result: %u %s", ret[0], ret[1])
                return uuid

            LOG.info("Result: %u %s", ret[0], ret[1])

        except ConnectionRefusedError:
            LOG.error("Intent interface not found")

        except Exception as ex:
            LOG.exception(ex)

        return None

    def remove_intent(self, uuid=None):
        """Remove intent."""

        if uuid:
            LOG.info("Removing intent: %s", uuid)
        else:
            LOG.info("Removing intent: ALL")

        try:

            conn = \
                http.client.HTTPConnection(self.intent_host, self.intent_port)

            if uuid:
                conn.request("DELETE", self.intent_url + "/%s" % uuid)
            else:
                conn.request("DELETE", self.intent_url)

            response = conn.getresponse()

            ret = (response.status, response.reason, response.read())

            LOG.info("Result: %u %s", ret[0], ret[1])
            conn.close()

        except ConnectionRefusedError:
            LOG.error("Intent interface not found")

        except Exception as ex:
            LOG.exception(ex)

    def to_dict(self):
        """ Return a dict representation of the object. """

        return {'port': self.port,
                'intent_host': self.intent_host,
                'intent_port': self.intent_port}


def launch(port=DEFAULT_PORT):
    """Start the Energino Server Module."""

    server = IntentServer(port)
    LOG.info("Intent Server available at %u", server.port)
    return server
