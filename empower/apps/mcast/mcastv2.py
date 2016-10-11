#!/usr/bin/env python3
#
# Copyright (c) 2016, Estefanía Coronado
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
import datetime
import sys

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.core.resourcepool import TX_MCAST
from empower.core.resourcepool import TX_MCAST_DMS
from empower.core.resourcepool import TX_MCAST_LEGACY
from empower.core.tenant import T_TYPE_SHARED
from empower.datatypes.etheraddress import EtherAddress
from empower.main import RUNTIME
from empower.apps.mcast.mcastwtp import MCastWTPInfo
from empower.apps.mcast.mcastclient import MCastClientInfo

import empower.logger
LOG = empower.logger.get_logger()

MCAST_PERIOD_100_900 = 0x00
MCAST_PERIOD_500_2500 = 0x01
MCAST_PERIOD_500_4500 = 0x02

MCAST_EWMA_PROB = 0x03
MCAST_CUR_PROB = 0x04


class MCast(EmpowerApp):


    """Energy consumption balacing app.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        (old) ./empower-runtime.py apps.mcast.mcast:52313ecb-9d00-4b7d-b873-b55d3d9ada26
        (new) ./empower-runtime.py apps.mcast.mcastrssi --tenant_id=be3f8868-8445-4586-bc3a-3fe5d2c17339

    """

    initial_time = time.time()

    def __init__(self, **kwargs):

        EmpowerApp.__init__(self, **kwargs)

        self.__mcast = 0
        self.__mcast_clients = []
        self.__mcast_wtps = [] 
        self.__prob_thershold = 95
        self.__period = MCAST_PERIOD_500_2500
        self.mcast_addr = "01:00:5e:00:00:fb"

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)
        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)
        self.wtpdown(callback=self.wtp_down_callback)

        if self.period == MCAST_PERIOD_100_900:
            self.period_length = 10
            self.legacy_length = 9
        elif self.period == MCAST_PERIOD_500_2500:
            self.period_length = 5
            self.legacy_length = 4
        elif self.period == MCAST_PERIOD_500_4500:
            self.period_length = 10
            self.legacy_length = 9

    @property
    def mcast(self):
        """Return current multicast period."""
        return self.__mcast

    @mcast.setter
    def mcast(self, mcast):
        self.__mcast = mcast

    @property
    def mcast_clients(self):
        """Return current multicast clients."""
        return self.__mcast_clients

    @mcast_clients.setter
    def mcast_clients(self, mcast_clients_info):
        self.__mcast_clients = mcast_clients_info

    @property
    def mcast_wtps(self):
        """Return current multicast wtps."""
        return self.__mcast_wtps

    @mcast_wtps.setter
    def mcast_wtps(self, mcast_wtps_info):
        self.__mcast_wtps = mcast_wtps_info

    @property
    def prob_thershold(self):
        """Return current probability thershold."""
        return self.__prob_thershold

    @prob_thershold.setter
    def prob_thershold(self, prob_thershold):
        self.__prob_thershold = prob_thershold

    @property
    def period(self):
        """Return current multicast DMS - Legacy period."""
        return self.__period

    @period.setter
    def period(self, period):
        self.__period = period


    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""
        for block in wtp.supports:
            if any(entry.block.hwaddr == block.hwaddr for entry in self.mcast_wtps):
                continue

            wtp_info = MCastWTPInfo()
            wtp_info.block = block
            wtp_info.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB
            self.mcast_wtps.append(wtp_info)


    def wtp_down_callback(self, wtp):
        """Called when a wtp connectdiss from the controller."""

        for index, entry in enumerate(self.mcast_wtps):
            for block in wtp.supports:
                if block.hwaddr == entry.block.hwaddr:
                    del self.mcast_wtps[index]
                    break


    def lvap_join_callback(self, lvap):
        """ New LVAP. """

        if any(lvap.addr == entry.addr for entry in self.mcast_clients):
            return

        lvap.lvap_stats(every=self.every, callback=self.lvap_stats_callback)

        default_block = next(iter(lvap.downlink))
        lvap_info = MCastClientInfo()
        lvap_info.addr = lvap.addr
        lvap_info.attached_hwaddr = default_block.hwaddr
        self.mcast_clients.append(lvap_info)

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == default_block.hwaddr:
                entry.attached_clients = entry.attached_clients + 1
                break

    def lvap_leave_callback(self, lvap):
        """Called when an LVAP disassociates from a tennant."""

        default_block = next(iter(lvap.downlink))

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == lvap.addr:
                del self.mcast_clients[index]
                break

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == default_block.hwaddr:
                entry.attached_clients = entry.attached_clients - 1
                break

        # In case this was the worst receptor, the date rate for legacy multicast must be recomputed
        if self.mcast_clients:
            self.legacy_mcast_compute()


    def lvap_stats_callback(self, counter):
        """ New stats available. """

        rates = (counter.to_dict())["rates"] 
        if not rates:
            return
        if counter.lvap not in RUNTIME.lvaps:
            return

        highest_prob = 0
        highest_rate = 0
        highest_cur_prob = 0
        sec_highest_rate = 0
        higher_thershold_ewma_rates = []
        higher_thershold_ewma_prob = []
        higher_thershold_cur_prob_rates = []
        higher_thershold_cur_prob = []
        lowest_rate = min(int(float(key)) for key in rates.keys())

        # Looks for the rate that has the highest ewma prob. for the station.
        # If two rates have the same probability, the highest one is selected. 
        # Stores in a list the rates whose ewma prob. is higher than a certain thershold.
        for key, entry in rates.items():  #key is the rate
            if (rates[key]["prob"] > highest_prob) or \
            (rates[key]["prob"] == highest_prob and int(float(key)) > highest_rate):
                highest_rate = int(float(key))
                highest_prob = rates[key]["prob"]
            if (int(float(rates[key]["prob"]))) >= self.prob_thershold:
                higher_thershold_ewma_rates.append(int(float(key)))
                higher_thershold_ewma_prob.append(rates[key]["prob"])

        # Looks for the rate that has the highest cur prob and is lower than the one selected
        # for the ewma prob for the station.
        # Stores in a list the rates whose cur prob. is higher than thershold%.
        for key, entry in rates.items():
            if rates[key]["cur_prob"] > highest_cur_prob or \
            (rates[key]["cur_prob"] == highest_cur_prob and int(float(key)) > sec_highest_rate):
                sec_highest_rate = int(float(key))
                highest_cur_prob = rates[key]["cur_prob"] 
            if (int(float(rates[key]["cur_prob"]))) >= self.prob_thershold:
                higher_thershold_cur_prob_rates.append(int(float(key)))
                higher_thershold_cur_prob.append(rates[key]["cur_prob"])     

        if highest_cur_prob == 0 and highest_prob == 0:
            highest_rate = lowest_rate
            sec_highest_rate = lowest_rate
        elif highest_cur_prob == 0 and highest_prob != 0:
            sec_highest_rate = highest_rate

        # Client info update
        lvap = RUNTIME.lvaps[counter.lvap]
        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == counter.lvap:
                entry.highest_rate = int(highest_rate)
                entry.rates = rates
                entry.highest_cur_prob_rate = int(sec_highest_rate)
                entry.higher_thershold_ewma_rates = higher_thershold_ewma_rates
                entry.higher_thershold_cur_prob_rates = higher_thershold_cur_prob_rates
                break


    def loop(self):
        """ Periodic job. """
        if not self.mcast_clients:
            for index, entry in enumerate(self.mcast_wtps):
                tx_policy = entry.block.tx_policies[EtherAddress(self.mcast_addr)]
                tx_policy.mcast = TX_MCAST_DMS
        else:
            if (self.mcast % self.period_length) < 1:
                for index, entry in enumerate(self.mcast_wtps):
                    tx_policy = entry.block.tx_policies[EtherAddress(self.mcast_addr)]
                    tx_policy.mcast = TX_MCAST_DMS
            else:
                self.legacy_mcast_compute()
                if (self.mcast % self.period_length) == self.legacy_length:
                    self.mcast = -1
            self.mcast += 1


    def multicast_rate(self, hwaddr):
        min_rate = sys.maxsize
        min_highest_cur_prob_rate = sys.maxsize
        thershold_intersection_list = []
        thershold_highest_cur_prob_rate_intersection_list = []
        highest_thershold_valid = True
        second_thershold_valid = True

        for index, entry in enumerate(self.mcast_clients):
            # It looks for the lowest rate among all the receptors just in case in there is no valid intersection
            # for the best rates of the clients (for both the ewma and cur probabilities). 
            if entry.highest_rate < min_rate:
                min_rate = entry.highest_rate
            if entry.highest_cur_prob_rate < min_highest_cur_prob_rate:
                min_highest_cur_prob_rate = entry.highest_cur_prob_rate

            # It checks if there is a possible intersection among the clients rates for the emwa prob.
            if highest_thershold_valid is True:
                # If a given client does not have any rate higher than the required prob (e.g. thershold% for emwa)
                # it is assumed that there is no possible intersection
                if not entry.higher_thershold_ewma_rates:
                    highest_thershold_valid = False
                elif not thershold_intersection_list:
                    thershold_intersection_list = entry.higher_thershold_ewma_rates
                else:
                    thershold_intersection_list = list(set(thershold_intersection_list) & set(entry.higher_thershold_ewma_rates))
                    if not thershold_intersection_list:
                        highest_thershold_valid = False
            # It checks if there is a possible intersection among the clients rates for the cur prob.
            if second_thershold_valid is True:
                # If a given client does not have any rate higher than the required prob (e.g. thershold% for cur prob)
                # it is assumed that there is no possible intersection
                if not entry.higher_thershold_cur_prob_rates:
                    second_thershold_valid = False
                elif not thershold_highest_cur_prob_rate_intersection_list:
                    thershold_highest_cur_prob_rate_intersection_list = entry.higher_thershold_cur_prob_rates
                else:
                    thershold_highest_cur_prob_rate_intersection_list = list(set(thershold_highest_cur_prob_rate_intersection_list) & set(entry.higher_thershold_cur_prob_rates))
                    if not thershold_highest_cur_prob_rate_intersection_list:
                        second_thershold_valid = False


        # If the old client was the only client in the wtp or there is not any client, lets have the basic rate
        if min_rate == sys.maxsize:
            for index, entry in enumerate(self.mcast_wtps):
                if entry.block.hwaddr == hwaddr:
                    min_rate = min(entry.block.supports)
                    min_highest_cur_prob_rate = min(entry.block.supports)
                    break

        return min_rate, min_highest_cur_prob_rate, thershold_intersection_list, thershold_highest_cur_prob_rate_intersection_list


    def legacy_mcast_compute(self):
        for index, entry in enumerate(self.mcast_wtps):

            # It obtains the most appropiate rate
            calculated_rate, highest_cur_prob_rate, thershold_intersection_list, thershold_highest_cur_prob_rate_intersection_list = self.multicast_rate(entry.block.hwaddr)
            
            # If some rates have been obtained as a result of the intersection, the highest one is selected as the rate. 
            if thershold_intersection_list:
                best_rate = max(thershold_intersection_list)
            # Otherwise, the rate selected is the minimum among the MRs
            else:
                best_rate = calculated_rate
            # The same happens for the cur prob. 
            if thershold_highest_cur_prob_rate_intersection_list:
                best_highest_cur_prob_rate = max(thershold_highest_cur_prob_rate_intersection_list)
            else:
                best_highest_cur_prob_rate = highest_cur_prob_rate

            entry.rate[self.mcast_addr] = best_rate
            entry.cur_prob_rate[self.mcast_addr] = best_highest_cur_prob_rate

            tx_policy = entry.block.tx_policies[EtherAddress(self.mcast_addr)]
            tx_policy.mcast = TX_MCAST_LEGACY

            # The rate is selected according to the probability used in that moment. 
            if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                tx_policy.mcs = [int(best_rate)]
            elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                tx_policy.mcs = [int(best_highest_cur_prob_rate)]


    def lvap_bssid_to_hwaddr(self, aps_info):
        aps_hwaddr_info = dict()
        shared_tenants = [x for x in RUNTIME.tenants.values()
                              if x.bssid_type == T_TYPE_SHARED]

        for key, value in aps_info.items():
            for tenant in shared_tenants:
                if EtherAddress(key) in tenant.vaps and tenant.vaps[EtherAddress(key)].block.hwaddr not in aps_hwaddr_info:
                    hwaddr = tenant.vaps[EtherAddress(key)].block.hwaddr
                    aps_hwaddr_info[hwaddr] = value

        return aps_hwaddr_info


    def attached_clients(self):
        nb_attached_clients = 0

        for index, entry in enumerate(self.mcast_wtps):
            nb_attached_clients = nb_attached_clients + entry.attached_clients

        return nb_attached_clients
    

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = super().to_dict()

        out['mcast_clients'] = []
        for p in self.mcast_clients:
            out['mcast_clients'].append(p.to_dict())
        out['mcast_wtps'] = []
        for p in self.mcast_wtps:
            out['mcast_wtps'].append(p.to_dict())

        return out
                                    


def launch(tenant_id, every=DEFAULT_PERIOD, mcast_clients=[], mcast_wtps=[]):
    """ Initialize the module. """

    return MCast(tenant_id=tenant_id, every=every, mcast_clients=mcast_clients, mcast_wtps=mcast_wtps)
