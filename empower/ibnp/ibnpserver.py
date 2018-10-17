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

from empower.datatypes.match import conflicting_match
from empower.ibnp.ibnpmainhandler import IBNPMainHandler
from empower.persistence import Session
from empower.persistence.persistence import TblTrafficRule

from empower.main import RUNTIME


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

        self.rules = {}

        self.__load_traffic_rules()

        handlers = []

        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler, dict(server=self)))

        tornado.web.Application.__init__(self, handlers)
        http_server = tornado.httpserver.HTTPServer(self)
        http_server.listen(self.port)

    def __load_traffic_rules(self):

        rules = Session().query(TblTrafficRule).all()

        for rule in rules:

            tenant = RUNTIME.tenants[rule.tenant_id]

            traffic_rule = TrafficRule(tenant=tenant,
                                       match=rule.match,
                                       priority=rule.priority,
                                       label=rule.label,
                                       dscp=rule.dscp)

            self.add_traffic_rule(traffic_rule)

    def add_traffic_rule(self, tr):
        """Send traffic rule to backhaul controller."""

        tenant_id = tr.tenant.tenant_id
        match = tr.match

        if tenant_id not in self.rules:
            self.rules[tenant_id] = {}

        if tr.priority > 50:
            raise ValueError('priority must not exceed 50')

        matches = [match for match in self.rules[tenant_id].keys()
                   if self.rules[tenant_id][match].priority == tr.priority]

        conflict = conflicting_match(matches, tr.match)
        if conflict:
            raise ValueError('match conflict: %s --> %s' % (tr.match, conflict))

        self.rules[tenant_id][match] = tr

        if self.connection:
            self.connection.send_add_tr(tr)

    def del_traffic_rule(self, tenant_id, match):
        """Remove traffic rule from backhaul controller."""

        if match in self.rules[tenant_id]:
            del self.rules[tenant_id][match]

        if self.connection:
            self.connection.send_remove_tr(tenant_id, match)

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
