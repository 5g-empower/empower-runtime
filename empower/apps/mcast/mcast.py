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

"""Multicast management app."""

import tornado.web
import tornado.httpserver
import time

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.core.resourcepool import TX_MCAST
from empower.core.resourcepool import TX_MCAST_DMS
from empower.core.resourcepool import TX_MCAST_LEGACY
from empower.datatypes.etheraddress import EtherAddress
from empower.apps.mcast import MCAST_RECEPTORS_BEST_RATES
from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

MCAST_PERIOD_100_900 = 0x0
MCAST_PERIOD_500_2500 = 0x1
MCAST_PERIOD_500_4500 = 0x2


class MCastIfaceInfo(object):
    def __init__(self, hwaddr):
        self._hwaddr = hwaddr
        self._stations_info = []

class MCast(EmpowerApp):


    """Energy consumption balacing app.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.mcast.mcast:52313ecb-9d00-4b7d-b873-b55d3d9ada26
        ./empower-runtime.py apps.mobilitymanager.mobilitymanager \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D

    """
    

    def __init__(self, **kwargs):

        self.mcast = 0

        self.period = MCAST_PERIOD_100_900

        if self.period == MCAST_PERIOD_100_900:
            self.period_length = 10
            self.legacy_length = 9
        elif self.period == MCAST_PERIOD_500_2500:
            self.period_length = 5
            self.legacy_length = 4
        elif self.period == MCAST_PERIOD_500_4500:
            self.period_length = 10
            self.legacy_length = 9

        EmpowerApp.__init__(self, **kwargs)

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)

        self.lvapleave(callback=self.lvap_leave_callback)

        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)

        self.wtpdown(callback=self.wtp_down_callback)


    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""
        for block in wtp.supports:
            hwaddr_info = MCastIfaceInfo(block.hwaddr)
            MCAST_RECEPTORS_BEST_RATES.append(hwaddr_info)


    def wtp_down_callback(self, wtp):
        """Called when a wtp connectdiss from the controller."""

        for index, entry in enumerate(MCAST_RECEPTORS_BEST_RATES):
            for block in wtp.supports:
                if block.hwaddr == entry._hwaddr:
                    del MCAST_RECEPTORS_BEST_RATES[index]


    def lvap_join_callback(self, lvap):
        """ New LVAP. """

        #lvap.lvap_stats(every=DEFAULT_PERIOD, callback=self.lvap_stats_callback)
        lvap.lvap_stats(every=self.every, callback=self.lvap_stats_callback)

        default_block = next(iter(lvap.scheduled_on.keys()))

        lvap_info = {
            'addr': lvap.addr,
            'rate': 1,
            'rates' : {}
        }

        for index, entry in enumerate(MCAST_RECEPTORS_BEST_RATES):
            if entry._hwaddr == default_block.hwaddr:
                entry._stations_info.append(lvap_info)
                break

    def lvap_leave_callback(self, lvap):
        """Called when an LVAP disassociates from a tennant."""

        default_block = next(iter(lvap.scheduled_on.keys()))

        for index, entry in enumerate(MCAST_RECEPTORS_BEST_RATES):
            if entry._hwaddr == default_block.hwaddr:
                for staIndex, staEntry in enumerate(entry._stations_info):
                    if staEntry['addr'] == lvap.addr:
                        del MCAST_RECEPTORS_BEST_RATES[index]._stations_info[staIndex]
                        break

        # In case this was the worst receptor, the date rate for legacy multicast must be recomputed
        self.legacyMcastCompute()

    def lvap_stats_callback(self, counter):
        """ New stats available. """
        # pick the rate with the highest probability
        rates = (counter.to_dict())["rates"]
        print("RATES", rates)
        if rates:
        #highest_rate = max(rates, key=rates.get)

            lowest_rate = min(float(key) for key in rates.keys())
            highest_prob = 0
            highest_rate = 0
            for key, entry in rates.items():
                if rates[key]["prob"] > highest_prob:
                    highest_rate = float(key)
                    highest_prob = rates[key]["prob"]
                elif rates[key]["prob"] == highest_prob:
                    if float(key) > highest_rate:
                        highest_rate = float(key)
                        highest_prob = rates[key]["prob"]

            if highest_prob == 0:
                highest_rate = lowest_rate

            if counter.lvap in RUNTIME.lvaps:
                lvap = RUNTIME.lvaps[counter.lvap]
                hwaddr = next(iter(lvap.scheduled_on.keys())).hwaddr

                for index, entry in enumerate(MCAST_RECEPTORS_BEST_RATES):
                    if entry._hwaddr == hwaddr:
                        for staIndex, staEntry in enumerate(entry._stations_info):
                            if staEntry['addr'] == counter.lvap:
                                staEntry['rate'] = int(highest_rate)
                                staEntry['rates'] = rates
                                break


    def loop(self):
        """ Periodic job. """
        #if (self.mcast % 5) < 1:
        if (self.mcast % self.period_length) < 1:
            for wtp in self.wtps():
                for block in wtp.supports:
                    tx_policy = block.tx_policies[EtherAddress("01:00:5e:00:00:fb")]
                    tx_policy.mcast = TX_MCAST_DMS
        else:
            self.legacyMcastCompute()
            #if (self.mcast % 5) == 4:
            if (self.mcast % self.period_length) == self.legacy_length:
                self.mcast = -1
        self.mcast += 1
        pass

    def multicastRate(self, hwaddr):
        if not MCAST_RECEPTORS_BEST_RATES:
            return 1
        for index, entry in enumerate(MCAST_RECEPTORS_BEST_RATES):
            if entry._hwaddr == hwaddr:
                if not entry._stations_info:
                    return 1
                #print("_stations_info", entry._stations_info)
                rate = min(int(sta['rate']) for sta in entry._stations_info)
                return rate

    def legacyMcastCompute(self):
        for wtp in self.wtps():
            for block in wtp.supports:
                rate = self.multicastRate(block.hwaddr)
                #print("NEW RATE", rate, block)
                tx_policy = block.tx_policies[EtherAddress("01:00:5e:00:00:fb")]
                tx_policy.mcast = TX_MCAST_LEGACY
                tx_policy.mcs = [int(rate)]
                #tx_policy.mcs = [36]
            #print("Changing policy to Legacy", int((time.time() - self.initial_time)))


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    #rest_server = RUNTIME.components[RESTServer.__module__]
    #rest_server.add_handler_class(MCastHandler, server)

    return MCast(tenant_id=tenant_id, every=every)
