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
            feed.pnfdev_addr = self.pnfdev.addr
        else:
            feed.pnfdev_addr = None

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
