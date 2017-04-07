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
        self.intent_url_rules = "/intent/rules"
        self.intent_url_poa = "/intent/poa"

        handlers = []
        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler))

        tornado.web.Application.__init__(self, handlers)
        http_server = tornado.httpserver.HTTPServer(self)
        http_server.listen(self.port)

        self.get_rule()
        self.get_poa()

        self.remove_rule()
        self.remove_poa()

    def __get_response(self, method, url, uuid=None, body=None):
        """Generic get intent."""

        conn = http.client.HTTPConnection(self.intent_host, self.intent_port)
        url = url + "/%s" % uuid if uuid else url
        headers = {}

        if body:
            body = json.dumps(body, indent=4, cls=EmpowerEncoder)
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
            }
            LOG.info("Intent %s %s:\n%s", method, url, body)
        else:
            LOG.info("Intent %s %s", method, url)

        conn.request(method, url, body, headers)
        response = conn.getresponse()
        location = response.getheader("Location", None)
        ret = (response.status, response.reason, location)
        LOG.info("Result: %u %s", ret[0], ret[1])
        conn.close()

        return ret

    def __get_intent(self, url, uuid=None):
        try:
            self.__get_response("GET", url, uuid)
        except ConnectionRefusedError:
            LOG.error("Intent interface not found")
        except Exception as ex:
            LOG.exception(ex)

    def get_rule(self, uuid=None):
        self.__get_intent(self.intent_url_rules, uuid)

    def get_poa(self, uuid=None):
        self.__get_intent(self.intent_url_poa, uuid)

    def __send_intent(self, method, url, intent, uuid=None):
        """Create new intent."""

        try:
            ret = self.__get_response(method, url, uuid, intent)
            if ret[0] == 201:
                url = urlparse(ret[2])
                uuid = UUID(url.path.split("/")[-1])
                return uuid
            if ret[0] == 204:
                return uuid
        except ConnectionRefusedError:
            LOG.warning("Intent interface not found")
        except Exception as ex:
            LOG.exception(ex)

        return None

    def add_rule(self, intent):
        return self.__send_intent(method="POST",
                                  url=self.intent_url_rules,
                                  intent=intent)

    def add_poa(self, intent):
        return self.__send_intent(method="POST",
                                  url=self.intent_url_poa,
                                  intent=intent)

    def update_rule(self, intent, uuid):
        self.__send_intent(method="PUT",
                           url=self.intent_url_rules,
                           intent=intent,
                           uuid=uuid)

    def update_poa(self, intent, uuid):
        self.__send_intent(method="PUT",
                           url=self.intent_url_poa,
                           intent=intent,
                           uuid=uuid)

    def __remove_intent(self, url, uuid=None):
        """Remove intent."""

        try:
            self.__get_response("DELETE", url, uuid)
        except ConnectionRefusedError:
            LOG.error("Intent interface not found")
        except Exception as ex:
            LOG.exception(ex)

    def remove_rule(self, uuid=None):
        self.__remove_intent(self.intent_url_rules, uuid)

    def remove_poa(self, uuid=None):
        self.__remove_intent(self.intent_url_poa, uuid)

    def to_dict(self):
        """ Return a dict representation of the object. """

        return {'port': self.port,
                'intent_host': self.intent_host,
                'intent_port': self.intent_port}


def launch(port=DEFAULT_PORT):
    """Start the Intent Server Module."""

    server = IntentServer(port)
    LOG.info("Intent Server available at %u", server.port)
    return server
