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
"""LoRa NS Discovery Protocol Server."""
import json
import logging
import tornado.websocket

from empower.core.eui64 import EUI64

LOG = logging.getLogger("LoRaNSDPMainHandler")


class LNSDPMainHandler(tornado.websocket.WebSocketHandler):
    """LNS Discovery Protocol Main Handler."""

    HANDLERS = [r"/router-info"]
    LABEL = "LoRaWAN NS Discovery Server"
    lgtw_id = None
    # This WS connection is dedicated to one lGtw TODO CHECK ASSUPTION TRUE
    lns_id = None
    uri = None
    error = None
    server = None

    @classmethod
    def urls(cls, **kwargs):
        """Return a list of handles."""
        return [
            (h, cls, kwargs) for h in cls.HANDLERS  # Route/Handler/kwargs
        ]

    def check_origin(self, origin):
        """Reject all requests with an origin on non specified hosts.

        Use this method a security protection against cross site scripting
        attacks on browsers, since WebSockets are allowed to bypass the
        usual same-origin policies and don’t use CORS headers.

        This is an important security measure: don’t disable it without
        understanding the security implications.

        In particular, if your authentication is cookie-based, you must
        either restrict the origins allowed by check_origin() or implement
        your own XSRF-like protection for websocket connections.
        See these articles for more:
        https://devcenter.heroku.com/articles/websocket-security
        http://www.tornadoweb.org/en/stable/websocket.html#configuration
        """
        # Alternative code:
        # allowed = ["https://site1.tld", "https://site2.tld"]
        # if origin not in allowed:
        #        return False
        return True

    def initialize(self, server):
        """Initialize server with custom arguments.

        This method is a hook for subclass initialization
        and Tornado will automatically call this method for each request.
        Therefore, this WebSocket connection is dedicated to a single lGtw.
        """
        self.server = server
        # Creation of variables moved to __init__
        LOG.info("%s initialized", self.LABEL)

    def to_dict(self):
        """Return dict representation of object."""
        return_value = {}
        return_value["router"] = self.lgtw_id
        return_value["muxs"] = self.lns_id
        return_value["uri"] = self.uri
        if self.error:
            return_value["error"] = self.error
        return return_value

    def open(self, *args: str, **kwargs: str):
        """Exec code when a new WebSocket is opened.

        The arguments to `open` are extracted from
        the `tornado.web.URLSpec` regular expression,
        just like the arguments to `tornado.web.RequestHandler.get`.
        """
        LOG.info("New WS LNS Discovery Protocol connection opened")

    def encode_message(self, message):
        """Encode JSON message."""
        self.write_message(json.dumps(message))

    def on_message(self, message):
        """Handle incoming message."""
        try:
            msg = json.loads(message)
            self.handle_message(msg)
        except ValueError:
            LOG.error("Invalid input: %s", message)

    def handle_message(self, msg):
        """Handle incoming message."""
        try:
            self.lgtw_id = EUI64(msg['router'])
        except KeyError:
            LOG.error(
                "Bad message formatting, 'router' information"
                "(Radio GTW EUI) missing")
            return

        LOG.info("New LNS discovery request from %s: %s",
                 self.lgtw_id, json.dumps(msg))

        self.send_lns_discovery_request_replay()

        return

    def send_lns_discovery_request_replay(self):
        """Execute a remote command on LGTW."""
        reply_message = {"router": self.lgtw_id.id6}
        for lns_euid in self.server.lnss:
            if self.lgtw_id in self.server.lnss[lns_euid].lgtws:
                reply_message["muxs"] = lns_euid.id6
                reply_message["router"] = self.lgtw_id.id6
                reply_message["uri"] = self.server.lnss[lns_euid].uri
                reply_message["uri"] += self.lgtw_id.id6
                break
        else:
            reply_message["error"] = "Unknown LoRaWAN Radio GTW ("
            reply_message["error"] += self.lgtw_id.id6 + ")"

        LOG.info("LNS Discovery Request reply: %s", json.dumps(reply_message))
        self.write_message(json.dumps(reply_message))

    def on_close(self):
        """Exec code when a existing WebSocket is closed."""
        LOG.error("WebSocket connection with %s closed", self.lgtw_id)
        self.lgtw_id = None
        self.lns_id = None
        self.uri = None
        self.error = None
