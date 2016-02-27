#!/usr/bin/env python3
#
# Copyright (c) 2016, Roberto Riggio
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

"""Virtual Power Metering App."""

import json
import os.path
import time

from datetime import datetime

from empower.core.app import EmpowerApp
from empower.core.app import EmpowerAppHandler
from empower.core.app import EmpowerAppHomeHandler
from empower.core.app import DEFAULT_PERIOD
from empower.events.lvapjoin import lvapjoin
from empower.counters.packets_counter import packets_counter

import empower.logger
LOG = empower.logger.get_logger()

MODES = {('11a', '20', 1): {'difs': 34,
                            'sifs': 16,
                            'slot': 9,
                            'min_cw': 15,
                            'symbol_duration': 4,
                            'bits_per_symbol': 216}}

DEFAULT_PROFILE = "./empower/apps/joule/models_30s_full.json"


class JouleHandler(EmpowerAppHandler):
    pass


class JouleHomeHandler(EmpowerAppHomeHandler):
    pass


class Joule(EmpowerApp):
    """Virtual Power Metering App.

    The extension does not actually perform any handover leaving the LVAP
    handover unchanged from the initial choice made by the controller.

    This extentions registers an RSSI trigger for all LVAP in the target
    pool(s) in order to be notified of new LVAP joining the network. The
    extension then registers two counters (bytes and packets) for every new
    LVAP. The extension then computes the power consumption of all LVAPs using
    the specifile profile.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)
        profile: path to the Joule profile as a json document

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.joule.joule:$ID \
            --profile=./empower/apps/joule/models_30s_full.json

    """

    MODULE_NAME = "joule"
    MODULE_HANDLER = JouleHandler
    MODULE_HOME_HANDLER = JouleHomeHandler

    def __init__(self, tenant, **kwargs):

        self.stats = {}
        self.prev_bins_tx = {}
        self.prev_bins_rx = {}
        self.power = {}
        self.created = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.updated = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.profile = None

        EmpowerApp.__init__(self, tenant, **kwargs)

        # load joule profile
        with open(os.path.expanduser(self.profile)) as json_data:
            self.profile = json.load(json_data)

        bins_with_eth = [x + 14 + 20 + 8 for x in self.profile['bins']]
        self.bins = sorted(bins_with_eth)

        # register a trigger of all lvaps, in this way as soon a new lvap
        # joins the pool this module will be promptly notified.
        lvapjoin(tenant_id=self.tenant.tenant_id,
                 callback=self.lvap_join_callback)

        self.last = time.time()

    def to_dict(self):
        """ Return object as power feed. """

        out = super().to_dict()

        feeds = {}

        for wtp in self.wtps():

            url = '/api/v1/tenants/%s/feeds/%s.json' % (self.tenant_id,
                                                        str(wtp.addr))
            feeds[wtp.addr] = {'created': self.created,
                               'updated': self.updated,
                               'datastreams': [],
                               'wtp': wtp.addr,
                               'feed': url}

            pwr = {'at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                   'id': 'power'}

            if not wtp.connection:
                pwr['current_value'] = 0.0
            else:
                pwr['current_value'] = self.profile['gamma']

            feeds[wtp.addr]['datastreams'].append(pwr)

        for lvap in self.stats:

            wtp_addr = self.lvap(lvap).wtp.addr

            feeds[wtp_addr]['datastreams'][0]['current_value'] = \
                feeds[wtp_addr]['datastreams'][0]['current_value'] + \
                self.power[lvap] - self.profile['gamma']

        out['feeds'] = {str(k): v for k, v in feeds.items()}

        return out

    def lvap_join_callback(self, lvap):
        """ Handle RSSI trigger event. """

        # track packets and bytes counter for the new LVAP
        packets_stats = packets_counter(bins=self.bins,
                                        tenant_id=self.tenant.tenant_id,
                                        lvap=lvap.addr,
                                        every=self.every)

        self.stats[lvap.addr] = packets_stats
        self.power[lvap.addr] = 0.0

    def loop(self):
        """ Periodic job. """

        delta = time.time() - self.last
        self.last = time.time()

        for sta in self.stats:

            bins_rx = self.stats[sta].rx_samples[:]
            bins_tx = self.stats[sta].tx_samples[:]

            if sta not in self.prev_bins_rx:
                self.prev_bins_rx[sta] = bins_rx

            if sta not in self.prev_bins_tx:
                self.prev_bins_tx[sta] = bins_tx

            power_rx = self.compute(bins_rx, self.prev_bins_rx[sta],
                                    'RX', delta)

            power_tx = self.compute(bins_tx, self.prev_bins_tx[sta],
                                    'TX', delta)

            self.prev_bins_rx[sta] = bins_rx[:]
            self.prev_bins_tx[sta] = bins_tx[:]

            self.power[sta] = power_tx + power_rx + self.profile['gamma']

            LOG.info("LVAP %s Power: %f", sta, self.power[sta])

        self.updated = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def compute(self, bins_curr, bins_prev, model, delta):
        """ Compute power consumption from bins. """

        power = 0.0

        diff = []
        for i in range(0, len(bins_curr)):
            diff.append(bins_curr[i] - bins_prev[i])

        for i in range(0, len(diff)):

            if diff[i] == 0.0:
                continue

            d_bytes = self.bins[i]
            x_mbps = ((d_bytes * diff[i] * 8) / delta) / 1000000

            alpha0 = self.profile[model]['alpha0']
            alpha1 = self.profile[model]['alpha1']

            d_bytes_str = str(d_bytes - 14 - 20 - 8)
            x_max = self.profile[model]['x_max'][d_bytes_str]

            LOG.info("%s: %u bytes, %u Mbps -> x_max %f [Mb/s]", model,
                     d_bytes,
                     x_mbps,
                     x_max)

            # this should be generalized
            if x_mbps < 0.1:
                continue

            if x_mbps > x_max:
                x_mbps = x_max

            alpha_d = alpha0 * (1 + (alpha1 / d_bytes))

            power = alpha_d * x_mbps

            LOG.info("%s: %u bytes, %u pkts, %f s -> %f [Mb/s] %f",
                     model, d_bytes, diff[i], delta, x_mbps, power)

        return power


def launch(tenant, profile=DEFAULT_PROFILE, period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return Joule(tenant, profile=profile, every=period)
