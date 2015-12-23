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

"""Application implementing an uplink stats tracker."""

import re

from empower.core.app import EmpowerApp
from empower.core.app import EmpowerAppHandler
from empower.core.app import DEFAULT_PERIOD
from empower.triggers.summary import summary

import empower.logger
LOG = empower.logger.get_logger()

DEFAULT_RATES = [12, 18, 24, 36, 48, 72, 96, 108]


class UplinkStatsHandler(EmpowerAppHandler):
    pass


class UplinkStats(EmpowerApp):
    """Application implementing an uplink stats tracker.

    Command Line Parameters:

        sta: address of the lvap to track (optional, default 00:18:de:cc:d3:40)
        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.uplinkstats.uplinkstats:$ID

    """

    MODULE_NAME = "uplinkstats"
    MODULE_HANDLER = UplinkStatsHandler

    def __init__(self, tenant, addrs, primary_link_dl,
                 link_dl, rates, payload, pk_rate, period):

        EmpowerApp.__init__(self, tenant, period)

        self.primary_link_dl = float(primary_link_dl)
        self.link_dl = float(link_dl)
        self.rates = [int(x) for x in rates.split(",")]
        self.payload = int(payload)
        self.pk_rate = int(pk_rate)
        self.addrs = addrs
        self.alpha = 0.6
        self.pkt_couters = {}
        self.unique = {}
        self.stats = {}
        self.period_us = 500000
        self.last_valid = {}
        self.suffix = "%0.2f_%0.2f_%s_%u_%u" % \
            (self.primary_link_dl,
             self.link_dl,
             "_".join([str(x) for x in self.rates]),
             self.payload,
             self.pk_rate)

        summary(lvaps=self.addrs,
                tenant_id=self.tenant.tenant_id,
                every=2000,
                rates=self.rates,
                callback=self.summary_callback)

    def update_stats(self):

        self.stats = {}

        if not self.last_valid:
            return

        min_valid = min(self.last_valid.values())

        for entry in sorted(self.pkt_couters):

            if entry > min_valid:
                break

            for wtp in self.pkt_couters[entry]:

                for rate in self.pkt_couters[entry][wtp]:

                    tot = len(self.unique[entry][rate])

                    count = \
                        self.pkt_couters[entry][wtp][rate]['this_successes']

                    rate_entry = self.pkt_couters[entry][wtp][rate]
                    rate_entry['this_attempts'] = tot

                    if tot:
                        rate_entry['this_prob'] = 100 * float(count) / tot
                    else:
                        rate_entry['this_prob'] = None

                if wtp not in self.stats:
                    self.stats[wtp] = {}

                for rate in self.pkt_couters[entry][wtp]:

                    rate_entry = self.pkt_couters[entry][wtp][rate]

                    if rate not in self.stats[wtp]:

                        if rate_entry['this_prob']:
                            this_prob = rate_entry['this_prob']
                        else:
                            this_prob = 0

                        self.stats[wtp][rate] = {'attempts': 0,
                                                 'successes': 0,
                                                 'ewma_prob': this_prob}

                    self.stats[wtp][rate]['this_successes'] = \
                        rate_entry['this_successes']

                    self.stats[wtp][rate]['this_attempts'] = \
                        rate_entry['this_attempts']

                    self.stats[wtp][rate]['this_prob'] = \
                        rate_entry['this_prob']

                    self.stats[wtp][rate]['successes'] = \
                        self.stats[wtp][rate]['successes'] + \
                        rate_entry['this_successes']

                    self.stats[wtp][rate]['attempts'] = \
                        self.stats[wtp][rate]['attempts'] + \
                        rate_entry['this_attempts']

                    if rate_entry['this_prob']:

                        ewma_prob = \
                            self.alpha * self.stats[wtp][rate]['ewma_prob'] + \
                            (1 - self.alpha) * rate_entry['this_prob']

                        self.stats[wtp][rate]['ewma_prob'] = round(ewma_prob)

                    filename = "./pl_%s_%s.csv" % (self.suffix,
                                                   re.sub(':', '', str(wtp)))

                    line = "%u %u\n" % (self.stats[wtp][rate]['ewma_prob'],
                                        self.stats[wtp][rate]['this_prob'])

                    with open(filename, 'a') as file_d:
                        file_d.write(line)

    def to_dict(self, *args):
        """ Return a JSON-serializable dictionary representing the summary """

        out = super().to_dict()

        out['stats'] = {str(j): w for j, w in self.stats.items()}

        return out

    def summary_callback(self, trigger):

        lvap = self.lvap(trigger.lvaps)
        wtp = lvap.wtp

        filename = "./sensor_%s_%s.csv" % (self.suffix,
                                           re.sub(':', '', str(wtp.addr)))

        if not trigger.first_tsft:
            return

        if wtp.addr not in self.last_valid:
            self.last_valid[wtp.addr] = trigger.first_tsft

        for frame in trigger.frames[lvap.addr][wtp.addr]:

            import random

            if wtp.addr == trigger.ref:
                if random.random() >= self.primary_link_dl:
                    continue
            else:
                if random.random() >= self.link_dl:
                    continue

            if frame['tsft_adj'] > self.last_valid[wtp.addr] + self.period_us:
                self.last_valid[wtp.addr] = self.last_valid[wtp.addr] + \
                    self.period_us

            tsft = self.last_valid[wtp.addr]

            if tsft not in self.pkt_couters:
                self.pkt_couters[tsft] = {}

            if tsft not in self.unique:
                self.unique[tsft] = {}

            if wtp.addr not in self.pkt_couters[tsft]:
                self.pkt_couters[tsft][wtp.addr] = {}

            if frame['rate'] not in self.pkt_couters[tsft][wtp.addr]:
                self.pkt_couters[tsft][wtp.addr][frame['rate']] = \
                    {'this_successes': 0}

            if frame['rate'] not in self.unique[tsft]:
                self.unique[tsft][frame['rate']] = set()

            rate = self.pkt_couters[tsft][wtp.addr][frame['rate']]
            rate['this_successes'] = rate['this_successes'] + 1

            self.unique[tsft][frame['rate']].add(frame['seq'])

            line = "%u %u %u %u %u %u %u %u\n" % (frame['tsft'],
                                                  frame['tsft_adj'],
                                                  frame['seq'],
                                                  frame['rate'],
                                                  frame['length'],
                                                  frame['dur'],
                                                  frame['type'],
                                                  frame['subtype'])

            with open(filename, 'a') as file_d:
                file_d.write(line)

        self.update_stats()


def launch(tenant,
           addrs="00:18:de:cc:d3:40",
           primary_link_dl=1.0,
           link_dl=1.0,
           rates=",".join([str(x) for x in DEFAULT_RATES]),
           payload=1472,
           pk_rate=100,
           period=DEFAULT_PERIOD):

    """ Initialize the module. """

    return UplinkStats(tenant,
                       addrs,
                       primary_link_dl,
                       link_dl,
                       rates,
                       payload,
                       pk_rate,
                       period)
