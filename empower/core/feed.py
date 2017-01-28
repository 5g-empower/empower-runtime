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

"""EmPOWER Feed Class."""

from datetime import datetime, timedelta
from tornado.httpclient import HTTPClient

from empower.persistence import Session
from empower.persistence.persistence import TblFeed

FEED_STATUS_ON = "on"
FEED_STATUS_OFF = "off"


class Feed(object):
    """Power consumption feed originating from an Energino."""

    def __init__(self, feed_id):

        self.feed_id = feed_id
        self.created = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.updated = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.private = False
        self.__pnfdev = None
        self.mngt = None
        self.datastreams = {}

    @property
    def pnfdev(self):
        """Return the PNFDev."""

        return self.__pnfdev

    @pnfdev.setter
    def pnfdev(self, pnfdev):
        """Set the PNFDev and update database."""

        self.__pnfdev = pnfdev

        session = Session()
        feed = Session().query(TblFeed) \
                        .filter(TblFeed.feed_id == self.feed_id) \
                        .first()
        if self.pnfdev:
            feed.addr = self.pnfdev.addr
        else:
            feed.addr = None

        session.commit()

    @property
    def is_on(self):
        """Return true if the switch is set to 0."""

        if not self.mngt:
            return None

        if 'switch' in self.datastreams:
            return self.datastreams['switch']['current_value'] == 0

    @is_on.setter
    def is_on(self, value):
        """Set the switch."""

        if not self.mngt:
            return

        if self.is_on == value:
            return

        if value:
            url = 'http://%s/arduino/datastreams/switch/%u' % (self.mngt[0], 0)
        else:
            url = 'http://%s/arduino/datastreams/switch/%u' % (self.mngt[0], 1)

        HTTPClient().fetch(url)

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the Feed."""

        last = datetime.strptime(self.updated, "%Y-%m-%dT%H:%M:%S.%fZ")
        now = datetime.now()
        delta = timedelta(seconds=30)

        if now - last > delta:
            status = 'dead'
        else:
            status = 'live'

        out = {'id': self.feed_id,
               'created': self.created,
               'updated': self.updated,
               'status': status,
               'datastreams': self.datastreams.values(),
               'feed': '/api/v1/feeds/%u.json' % (self.feed_id),
               'mngt': self.mngt}

        if self.pnfdev:
            out[self.pnfdev.SOLO] = self.pnfdev.addr

        return out

    def update(self, datastreams):
        """Update the datastrem with new samples.

        Args:
            datastreams, list of datastream objects.

        Returns:
            None

        Raises:
            ValueError: if am invalid datastream is passed.
        """

        self.updated = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        for incoming in datastreams:

            if incoming['id'] in self.datastreams:

                local = self.datastreams[incoming['id']]
                local['at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                local['current_value'] = incoming['current_value']

                if local['max_value'] < local['current_value']:
                    local['max_value'] = local['current_value']
                if local['min_value'] > local['current_value']:
                    local['min_value'] = local['current_value']

            else:

                self.datastreams[incoming['id']] = \
                    {'at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                     'max_value': incoming['current_value'],
                     'min_value': incoming['current_value'],
                     'id': incoming['id'],
                     'current_value': incoming['current_value']}

    def __str__(self):
        return str(self.feed_id)

    def __hash__(self):
        return hash(self.feed_id)

    def __eq__(self, other):
        if isinstance(other, Feed):
            return self.feed_id == other.feed_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
