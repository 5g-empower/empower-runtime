#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""WiFi Rate Control Statistics Primitive."""

from construct import Struct, Int8ub, Int16ub, Int32ub, Bytes, Array
from construct import Container

import empower.managers.ranmanager.lvapp as lvapp

from empower.core.etheraddress import EtherAddress
from empower.core.app import EApp
from empower.core.app import EVERY


PT_WIFI_RC_STATS_REQUEST = 0x80
PT_WIFI_RC_STATS_RESPONSE = 0x81

WIFI_RC_STATS_REQUEST = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "sta" / Bytes(6),
)
WIFI_RC_STATS_REQUEST.name = "wifi_rc_stats_request"

RC_ENTRY = Struct(
    "rate" / Int8ub,
    "prob" / Int32ub,
    "cur_prob" / Int32ub,
    "cur_tp" / Int32ub,
    "last_attempts" / Int32ub,
    "last_successes" / Int32ub,
    "hist_attempts" / Int32ub,
    "hist_successes" / Int32ub
)
RC_ENTRY.name = "rc_entry"

WIFI_RC_STATS_RESPONSE = Struct(
    "version" / Int8ub,
    "type" / Int8ub,
    "length" / Int32ub,
    "seq" / Int32ub,
    "xid" / Int32ub,
    "device" / Bytes(6),
    "iface_id" / Int32ub,
    "sta" / Bytes(6),
    "nb_entries" / Int16ub,
    "stats" / Array(lambda ctx: ctx.nb_entries, RC_ENTRY),
)
WIFI_RC_STATS_RESPONSE.name = "wifi_rc_stats_response"


class RCStats(EApp):
    """WiFi Rate Control Statistics Primitive.

    This primitive collects the RC statistics from the specified LVAP.

    Parameters:
        service_id: the service id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)
        sta: the LVAP to track as an EtherAddress (mandatory)
        every: the loop period in ms (optional, default 2000ms)

    Callbacks:
        rates: called everytime new measurement is processed
        best_prob: called everytime new measurement is processed

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.primitives.wifircstats.wifircstats",
            "params": {
                "sta": "11:22:33:44:55:66",
                "every": 2000
            }
        }
    """

    def __init__(self, service_id, project_id, sta, every=EVERY):

        super().__init__(service_id=service_id,
                         project_id=project_id,
                         sta=sta,
                         every=every)

        # Register messages
        lvapp.register_message(PT_WIFI_RC_STATS_REQUEST,
                               WIFI_RC_STATS_REQUEST)
        lvapp.register_message(PT_WIFI_RC_STATS_RESPONSE,
                               WIFI_RC_STATS_RESPONSE)

        # Data structures
        self.rates = {}
        self.best_prob = None
        self.best_tp = None

    @property
    def sta(self):
        """ Return the station address. """

        return self.params['sta']

    @sta.setter
    def sta(self, sta):
        """ Set the station address. """

        self.params['sta'] = EtherAddress(sta)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = super().to_dict()

        out['sta'] = self.sta
        out['rates'] = self.rates
        out['best_prob'] = self.best_prob
        out['best_tp'] = self.best_tp

        return out

    def loop(self):
        """Send out requests"""

        if self.sta not in self.context.lvaps:
            return

        lvap = self.context.lvaps[self.sta]

        msg = Container(length=WIFI_RC_STATS_REQUEST.sizeof(),
                        sta=lvap.addr.to_raw())

        lvap.wtp.connection.send_message(PT_WIFI_RC_STATS_REQUEST,
                                         msg,
                                         self.handle_response)

    def handle_response(self, response, *_):
        """Handle WIFI_RC_STATS_RESPONSE message."""

        lvap = self.context.lvaps[self.sta]

        # update this object
        self.rates = {}
        self.best_prob = None
        self.best_tp = None

        for entry in response.stats:

            rate = entry.rate if lvap.ht_caps else entry.rate / 2.0

            value = {
                'prob': entry.prob / 180.0,
                'cur_prob': entry.cur_prob / 180.0,
                'cur_tp': entry.cur_tp / ((18000 << 10) / 96) / 10,
                'last_attempts': entry.last_attempts,
                'last_successes': entry.last_successes,
                'hist_attempts': entry.hist_attempts,
                'hist_successes': entry.hist_successes,
            }

            self.rates[rate] = value

            # log
            row = [self.sta,
                   rate,
                   self.rates[rate]['prob'],
                   self.rates[rate]['cur_prob'],
                   self.rates[rate]['cur_tp'],
                   self.rates[rate]['last_attempts'],
                   self.rates[rate]['last_successes'],
                   self.rates[rate]['hist_attempts'],
                   self.rates[rate]['hist_successes']]

        # compute statistics
        self.best_prob = \
            max(self.rates.keys(), key=(lambda key: self.rates[key]['prob']))

        self.best_tp = \
            max(self.rates.keys(), key=(lambda key: self.rates[key]['cur_tp']))

        # handle callbacks
        self.handle_callbacks()


def launch(service_id, project_id, sta, every=EVERY):
    """ Initialize the module. """

    return RCStats(service_id=service_id, project_id=project_id, sta=sta,
                   every=every)
