#!/usr/bin/env python3
#
# Copyright (c) 2018 Giovanni Baggio

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

"""IBN Protocol Server."""

import tornado.web
import tornado.ioloop
import tornado.websocket

from empower.core.trafficrule import TrafficRule

from empower.ibnp.ibnpmainhandler import IBNPMainHandler
from empower.persistence import Session
from empower.persistence.persistence import TblTrafficRule


DEFAULT_PORT = 4444


class IBNPServer(tornado.web.Application):
    """Exposes the EmPOWER IBN API."""

    handlers = [IBNPMainHandler]

    def __init__(self, port):

        self.connection = None

        self.port = port
        self.period = None
        self.last_seen = None
        self.last_seen_ts = None
        self.__seq = 0

        self.trs = {}

        self.__load_traffic_rules()

        handlers = []

        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler, dict(server=self)))

        tornado.web.Application.__init__(self, handlers)
        http_server = tornado.httpserver.HTTPServer(self)
        http_server.listen(self.port)

    def __load_traffic_rules(self):

        trs = Session().query(TblTrafficRule).all()

        for rule_db in trs:

            tr = TrafficRule(ssid=rule_db.tenant_id,
                             match=rule_db.match,
                             label=rule_db.label,
                             dscp=rule_db.dscp)

            self.add_traffic_rule(tr)

    def add_traffic_rule(self, tr):

        tenant_id = tr.ssid
        match = tr.match

        if tenant_id not in self.trs:
            self.trs[tenant_id] = {}

        self.trs[tenant_id][match] = tr

        if self.connection:
            self.connection.add_tr(tr)

    def del_traffic_rule(self, tenant_id, match):

        if match in self.trs[tenant_id]:
            del self.trs[tenant_id][match]

        if self.connection:
            self.connection.remove_tr(tenant_id, match)

    @property
    def seq(self):
        """Return new sequence id."""

        self.__seq += 1
        return self.__seq

    def to_dict(self):
        """ Return a dict representation of the object. """

        out = {}
        out['port'] = self.port
        return out


def launch(port=DEFAULT_PORT):
    """Start IBNP Server Module. """

    server = IBNPServer(int(port))
    return server
