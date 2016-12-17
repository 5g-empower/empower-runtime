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

"""Energino server module."""

import tornado.web

from tornado import gen
from sqlalchemy.sql import func
from tornado.web import HTTPError
from tornado.web import asynchronous
from tornado.httpclient import AsyncHTTPClient

from empower.persistence.persistence import TblFeed
from empower.persistence.persistence import TblPNFDev
from empower.persistence import Session
from empower.core.feed import Feed
from empower.restserver.apihandlers import EmpowerAPIHandler
from empower.datatypes.etheraddress import EtherAddress
from empower.restserver.restserver import RESTServer
from empower.restserver.restserver import exceptions

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

DEFAULT_PORT = 5533


class FeedHandler(EmpowerAPIHandler):
    """Feeds handler."""

    HANDLERS = [r"/api/v1/feeds/?",
                r"/api/v1/feeds/([0-9]*)/?"]

    @exceptions
    def get(self, *args, **kwargs):
        """List all Feeds or just the specified one.

        Args:
            [0]: the feed id (optional)

        Example URLs:

            GET /api/v1/feeds
            GET /api/v1/feeds/1
        """

        if len(args) > 1:
            raise ValueError("Invalid URL")

        if len(args) == 0:
            self.write_as_json(RUNTIME.feeds.values())
        else:
            feed_id = int(args[0])
            self.write_as_json(RUNTIME.feeds[feed_id])

    @asynchronous
    @gen.engine
    def put(self, *args, **kwargs):
        """Update a feed configuration.

        This can be used to both bind the feed to a new PNFDEV and to turn
        on/off the power meter;

        Args:
            [0]: the feed id (mandatory)

        Request:
            version: protocol version (1.0)
            addr: the PNFDEV to which this feed must be bind_feed
            value: the status of the power meter (0=on, 1=off)

        Example URLs:

            PUT /api/v1/feeds/1
        """
        try:

            if len(args) != 1:
                raise ValueError("Invalid URL")

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("Missing version element")

            feed_id = int(args[0])

            if "addr" in request:

                # requester is setting new pnfdev
                if request["addr"] != "":
                    self.server.bind_feed(feed_id,
                                          EtherAddress(request["addr"]))
                else:
                    self.server.bind_feed(feed_id)

                self.set_status(204, None)
                self.finish()

            elif "value" in request:

                feed = RUNTIME.feeds[feed_id]

                # requester turning the feed on/off
                url = 'http://%s/arduino/datastreams/switch/%u'
                if not feed.mngt:
                    self.send_error(404)
                    return
                value = int(request['value'])
                try:
                    http_client = AsyncHTTPClient()
                    yield http_client.fetch(url % (feed.mngt[0], value))
                except HTTPError as ex:
                    self.send_error(ex.code)
                    return
                feed.update([{'id': 'switch', 'current_value': value}])
                self.write_as_json(feed)
                self.set_status(204, None)
                self.finish()

            else:

                raise ValueError("addr/status not specified")

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

    @exceptions
    def post(self, *args, **kwargs):
        """Create a new feed.

        The address of the new feed is provided in the Location header.

        Args:
            None

        Request:
            version: protocol version (1.0)

        Example URLs:

            POST /api/v1/feeds
        """

        if len(args) != 0:
            raise ValueError("Invalid URL")

        request = tornado.escape.json_decode(self.request.body)

        if "version" not in request:
            raise ValueError("missing version element")

        feed = self.server.add_feed()
        self.set_header("Location", "/api/v1/feeds/%s" % feed.feed_id)

        self.set_status(201, None)

    @exceptions
    def delete(self, *args, **kwargs):
        """Delete a feed.

        If no feed id is provided this method deletes all the feeds.

        Args:
            [0]: the feed id (optional)

        Example URLs:

            DELETE /api/v1/feeds
            DELETE /api/v1/feeds/1
        """

        if args:
            feed_id = int(args[0])
            self.server.remove_feed(feed_id)
        else:
            for feed_id in RUNTIME.feeds:
                self.server.remove_feed(feed_id)
            self.server.feed_id = 0

        self.set_status(204, None)


class EnerginoDatastreamsHandler(tornado.web.RequestHandler):
    """Datastreams handler."""

    HANDLERS = [r"/v2/feeds/([0-9]*).csv"]

    def put(self, *args, **kwargs):
        try:
            if len(args) != 1:
                raise ValueError("Invalid url")
            feed = RUNTIME.feeds[int(args[0])]
            datastreams = []
            data = self.request.body.decode('UTF-8')
            for entry in data.split("\n"):
                if entry == '':
                    continue
                stream = entry.split(",")
                if len(stream) != 2:
                    continue
                datastreams.append({'id': stream[0],
                                    'current_value': float(stream[1])})
            feed.update(datastreams)
            feed.mngt = (self.request.remote_ip, 80)
        except KeyError as ex:
            self.send_error(404, message=ex)
        self.set_status(204, None)


class EnerginoServer(tornado.web.Application):
    """Energino Server.

    Simple server implementing just the put method of the Xively interface.
    used to support power consumption monitoring feeds coming from Energino
    Yun and Energino Ethernet devices.
    """

    handlers = [EnerginoDatastreamsHandler]

    def __init__(self, port):

        self.port = int(port)
        self.__feed_id = 0

        handlers = []

        for handler in self.handlers:
            for url in handler.HANDLERS:
                handlers.append((url, handler))

        tornado.web.Application.__init__(self, handlers)
        http_server = tornado.httpserver.HTTPServer(self)
        http_server.listen(self.port)

        self.__load_feeds()

    @property
    def feed_id(self):
        """Return new feed id."""
        self.__feed_id += 1
        return self.__feed_id

    @feed_id.setter
    def feed_id(self, value):
        """Set the feed id."""
        self.__feed_id = value

    def bind_feed(self, feed_id, addr=None):
        """Bind Feed to PNFDev."""

        if feed_id not in RUNTIME.feeds:
            raise KeyError(feed_id)

        feed = RUNTIME.feeds[feed_id]

        # if the feed is pointing to a dev, then reset the feed attribute of
        # that dev to None
        if feed.pnfdev:

            pnfdev = Session().query(TblPNFDev) \
                .filter(TblPNFDev.addr == EtherAddress(feed.pnfdev.addr)) \
                .first()

            if pnfdev:
                pnfdevs = getattr(RUNTIME, pnfdev.tbl_type)
                pnfdevs[feed.pnfdev.addr].feed = None

        # reset fedd pnfdev attribute to none
        feed.pnfdev = None

        # set the new pnfdev
        if addr:

            pnfdev = Session().query(TblPNFDev) \
                .filter(TblPNFDev.addr == EtherAddress(addr)) \
                .first()

            if not pnfdev:
                raise KeyError(addr)

            pnfdevs = getattr(RUNTIME, pnfdev.tbl_type)

            pnfdev = pnfdevs[addr]
            feed.pnfdev = pnfdev
            pnfdev.feed = feed

    def __load_feeds(self):
        """Load Feeds."""

        for feed in Session().query(TblFeed).all():

            RUNTIME.feeds[feed.feed_id] = Feed(feed.feed_id)
            RUNTIME.feeds[feed.feed_id].created = feed.created
            RUNTIME.feeds[feed.feed_id].updated = feed.updated

            if feed.addr:

                pnfdev = Session().query(TblPNFDev) \
                    .filter(TblPNFDev.addr == EtherAddress(feed.addr)) \
                    .first()

                if pnfdev:

                    pnfdevs = getattr(RUNTIME, pnfdev.tbl_type)

                    RUNTIME.feeds[feed.feed_id].pnfdev = \
                        pnfdevs[feed.addr]
                    pnfdev = pnfdevs[feed.addr]
                    pnfdev.feed = RUNTIME.feeds[feed.feed_id]

                else:

                    session = Session()
                    delete = Session().query(TblFeed) \
                        .filter(TblFeed.feed_id == feed.feed_id) \
                        .first()
                    delete.pnfdev = None
                    session.commit()

        query = Session().query(
            TblFeed, func.max(TblFeed.feed_id).label("max_id"))

        if query.one().max_id:
            self.feed_id = int(query.one().max_id)

    def add_feed(self):
        """Create new Feed."""

        feed_id = self.feed_id
        RUNTIME.feeds[feed_id] = Feed(feed_id)
        session = Session()
        session.add(TblFeed(feed_id=feed_id,
                            created=RUNTIME.feeds[feed_id].created,
                            updated=RUNTIME.feeds[feed_id].updated))
        session.commit()

        return RUNTIME.feeds[feed_id]

    def remove_feed(self, feed_id):
        """Remove Feed."""

        if feed_id not in RUNTIME.feeds:
            raise KeyError(feed_id)

        self.bind_feed(feed_id)
        del RUNTIME.feeds[feed_id]

        feed = Session().query(TblFeed) \
                        .filter(TblFeed.feed_id == feed_id) \
                        .first()

        session = Session()
        session.delete(feed)
        session.commit()

    def to_dict(self):
        """ Return a dict representation of the object. """

        return {'port': self.port}


def launch(port=DEFAULT_PORT):
    """Start the Energino Server Module."""

    server = EnerginoServer(port)

    rest_server = RUNTIME.components[RESTServer.__module__]
    rest_server.add_handler_class(FeedHandler, server)

    LOG.info("Energino Server available at %u", server.port)

    return server
