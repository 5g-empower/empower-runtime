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

"""Multicast management app with handover support."""

import tornado.web
import tornado.httpserver
import time
import datetime
import sys
import statistics

from empower.core.app import EmpowerApp
from empower.core.resourcepool import TX_MCAST
from empower.core.resourcepool import TX_MCAST_DMS
from empower.core.resourcepool import TX_MCAST_LEGACY
from empower.core.resourcepool import TX_MCAST_DMS_H
from empower.core.resourcepool import TX_MCAST_LEGACY_H
from empower.core.tenant import T_TYPE_SHARED
from empower.datatypes.etheraddress import EtherAddress
from empower.main import RUNTIME
from empower.apps.mcast.mcastwtp import MCastWTPInfo
from empower.apps.mcast.mcastclient import MCastClientInfo
from empower.core.resourcepool import BT_L20

import empower.logger
LOG = empower.logger.get_logger()

MCAST_EWMA_PROB = "ewma"
MCAST_CUR_PROB = "cur_prob"


class MCastManager(EmpowerApp):


    """Multicast app with rate adaptation support.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        (old) ./empower-runtime.py apps.mcast.mcast:52313ecb-9d00-4b7d-b873-b55d3d9ada26
        (new) ./empower-runtime.py apps.mcast.mcastsimple_130217 --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada00

    """

    def __init__(self, **kwargs):

        EmpowerApp.__init__(self, **kwargs)
        self.__mcast_clients = []
        self.__mcast_wtps = []
        self.__prob_thershold = 95
        self.__mcast_addr = EtherAddress("01:00:5e:00:c8:dd")
        self.__ht_rates = True

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)
        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)
        self.wtpdown(callback=self.wtp_down_callback)

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
    def mcast_addr(self):
        """Return mcast_addr used."""
        return self.__mcast_addr

    @mcast_addr.setter
    def mcast_addr(self, mcast_addr):
        self.__mcast_addr = mcast_addr

    @property
    def ht_rates(self):
        """Return True if the ht_rates are used."""
        return self.__ht_rates

    @ht_rates.setter
    def ht_rates(self, ht_rates):
        self.__ht_rates = ht_rates

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""
        for block in wtp.supports:
            if any(entry.block.hwaddr == block.hwaddr for entry in self.mcast_wtps):
                continue

            wtp_info = MCastWTPInfo()
            wtp_info.block = block
            wtp_info.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB
            wtp_info.mode = TX_MCAST_DMS_H
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

        self.lvap_stats(lvap=lvap.addr,
                        every=self.every,
                        callback=self.lvap_stats_callback)

        default_block = lvap.blocks[0]
        lvap_info = MCastClientInfo()

        print("---JOIN---")

        lvap_info.addr = lvap.addr
        lvap_info.attached_hwaddr = default_block.hwaddr
        self.mcast_clients.append(lvap_info)

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == default_block.hwaddr:
                entry.attached_clients = entry.attached_clients + 1
                break

        if lvap.supported_band == BT_L20:
            self.ht_rates = False

    def lvap_leave_callback(self, lvap):
        """Called when an LVAP disassociates from a tennant."""

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == lvap.addr:
                del self.mcast_clients[index]
                break

        default_block = lvap.blocks[0]
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr != default_block.hwaddr:
                continue
            entry.attached_clients = entry.attached_clients - 1
            if entry.attached_clients == 0:
                return

            # In case that this was not the only client attached to this WTP, the rate must be recomputed.
            tx_policy = entry.block.tx_policies[self.mcast_addr]
            ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
            tx_policy.mcast = TX_MCAST_LEGACY
            if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                tx_policy.mcs = [int(ewma_rate)]
            elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                tx_policy.mcs = [int(cur_prob_rate)]
            entry.rate[self.mcast_addr] = ewma_rate
            entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
            entry.mode = TX_MCAST_LEGACY_H


    def lvap_stats_callback(self, counter):
        """ New stats available. """

        rates = (counter.to_dict())["rates"]
        if not rates or counter.lvap not in RUNTIME.lvaps:
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

        print("---RATES---", rates)

        # Looks for the rate that has the highest ewma prob. for the station.
        # If two rates have the same probability, the highest one is selected.
        # Stores in a list the rates whose ewma prob. is higher than a certain thershold.
        higher_thershold_ewma_rates[:] = []
        higher_thershold_ewma_prob[:] = []
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
        # Stores in a list the rates whose cur prob. is higher than thershold.

        higher_thershold_cur_prob_rates[:] = []
        higher_thershold_cur_prob[:] = []
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

        # The information of the client is updated with the new statistics
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
                tx_policy = entry.block.tx_policies[self.mcast_addr]
                tx_policy.mcast = TX_MCAST_DMS
        else:
            for index, entry in enumerate(self.mcast_wtps):
                tx_policy = entry.block.tx_policies[self.mcast_addr]

                # If there is no clients, the default mode is DMS
                # If there are many clients per AP, it combines DMS and legacy to obtain statistics.
                # If the AP is in DMS mode and the has been an update of the RSSI, the mode is changed to legacy.
                if entry.attached_clients == 0 or \
                (entry.mode == TX_MCAST_DMS_H and (entry.current_period % (entry.dms_max_period + entry.legacy_max_period)) < 1):
                    tx_policy.mcast = TX_MCAST_DMS
                    entry.mode = TX_MCAST_DMS_H
                else:
                    ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
                    tx_policy.mcast = TX_MCAST_LEGACY
                    if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                        if self.ht_rates:
                            tx_policy.ht_mcs = [int(ewma_rate)]
                        else:
                            tx_policy.mcs = [int(ewma_rate)]
                    elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                        if self.ht_rates:
                            tx_policy.ht_mcs = [int(cur_prob_rate)]
                        else:
                            tx_policy.mcs = [int(cur_prob_rate)]
                    entry.rate[self.mcast_addr] = ewma_rate
                    entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
                    entry.mode = TX_MCAST_LEGACY_H

                    if (entry.current_period % (entry.dms_max_period + entry.legacy_max_period)) == entry.legacy_max_period:
                        entry.current_period = -1

                if entry.attached_clients > 0:
                    entry.current_period += 1


    def calculate_wtp_rate(self, mcast_wtp):
        min_rate = best_rate = min_highest_cur_prob_rate = best_highest_cur_prob_rate = sys.maxsize
        thershold_intersection_list = []
        thershold_highest_cur_prob_rate_intersection_list = []
        highest_thershold_valid = True
        second_thershold_valid = True

        for index, entry in enumerate(self.mcast_clients):
            if entry.attached_hwaddr == mcast_wtp.block.hwaddr:
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
        if min_rate == sys.maxsize or min_rate == 0:
            for index, entry in enumerate(self.mcast_wtps):
                if entry.block.hwaddr == mcast_wtp.block.hwaddr:
                    min_rate = min(entry.block.supports)
                    min_highest_cur_prob_rate = min(entry.block.supports)
                    break

        # If some rates have been obtained as a result of the intersection, the highest one is selected as the rate.
        if thershold_intersection_list:
            best_rate = max(thershold_intersection_list)
        # Otherwise, the rate selected is the minimum among the MRs
        else:
            best_rate = min_rate
        # The same happens for the cur prob.
        if thershold_highest_cur_prob_rate_intersection_list:
            best_highest_cur_prob_rate = max(thershold_highest_cur_prob_rate_intersection_list)
        else:
            best_highest_cur_prob_rate = min_highest_cur_prob_rate

        return best_rate, best_highest_cur_prob_rate


    def to_dict(self):
        """Return JSON-serializable representation of the object."""
        out = super().to_dict()

        out['mcast_clients'] = []
        for p in self.mcast_clients:
            out['mcast_clients'].append(p.to_dict())
        out['mcast_wtps'] = []
        for p in self.mcast_wtps:
            out['mcast_wtps'].append(p.to_dict())
        out['mcast_addr'] = self.mcast_addr

        return out


def launch(tenant_id, every=1000, mcast_clients=[], mcast_wtps=[]):
    """ Initialize the module. """

    return MCastManager(tenant_id=tenant_id, every=every, mcast_clients=mcast_clients, mcast_wtps=mcast_wtps)
