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
        self.__rssi = {} # {client:rssi, client:rssi...}
        self.__rx_pkts = {} # {client:pkts, client:pkts...}
        self.__aps = {} # {client: {ap:rssi, ap:rssi...}, client: {ap:rssi, ap:rssi...}...}
        self.__mcast_clients = []
        self.__mcast_wtps = [] 
        self.__prob_thershold = 95
        self.__rssi_stabilizing_period = 5
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
    def rssi(self):
        """Return loop period."""
        return self.__rssi

    @rssi.setter
    def rssi(self, rssi_info):
        """Updates the rate according to the rssi"""

        if not rssi_info:
            return

        station = rssi_info['addr']
        if not EtherAddress(station) in RUNTIME.lvaps:
            return
       
        lvap = RUNTIME.lvaps[EtherAddress(station)]
        hwaddr = next(iter(lvap.downlink.keys())).hwaddr

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == EtherAddress(station):
                entry.rssi = rssi_info['rssi']
                break

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == hwaddr:
                entry.last_rssi_change = time.time()
                entry.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
                break 

        self.__rssi[station]= rssi_info['rssi']

        # If this message has been received from any client, it means its position has changed and
        # hence the rate must be recomputed. 
        self.legacy_mcast_compute()
        self.mcast = 0


    @property
    def rx_pkts(self):
        """Return loop period."""
        return self.__rx_pkts

    @rx_pkts.setter
    def rx_pkts(self, rx_pkts_info):
        """Updates the rate according to the rx_pkts received"""

        if not rx_pkts_info:
            return

        station = rx_pkts_info['addr']
        if not EtherAddress(station) in RUNTIME.lvaps:
            return

        attached_wtp_rx_pkts = 0
        stats = rx_pkts_info['stats']
        lvap = RUNTIME.lvaps[EtherAddress(station)]
        hwaddr = next(iter(lvap.downlink.keys())).hwaddr
        wtp_ix = -1

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.addr == hwaddr:
                attached_wtp_rx_pkts = entry.last_rx_pkts
                wtp_ix = index
                break

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                entry.rx_pkts = stats
                # It maches the received packets agains the amount of them sent by the WTP 
                # to a given multicast address
                self.rx_pkts_matching(attached_wtp_rx_pkts, hwaddr, wtp_ix)
                break

        self.__rx_pkts[station] = stats

    @property
    def aps(self):
        """Return loop period."""
        return self.__aps

    @aps.setter
    def aps(self, aps_info):
        """Updates the rate according to the aps information received"""
        if not aps_info:
            return

        station = aps_info['addr'] 
        attached_hwaddr = None

        if EtherAddress(station) not in RUNTIME.lvaps:
            return

        lvap = RUNTIME.lvaps[EtherAddress(station)]
        stats = self.lvap_bssid_to_hwaddr(aps_info['wtps'])
        nb_clients = self.attached_clients()

        # If there is only one AP is not worthy to do the process
        if len(stats) == 1:
            return

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == EtherAddress(station):
                entry.wtps = stats
                attached_hwaddr = entry.attached_hwaddr
                self.__aps[station] = stats

        if nb_clients > 1:
            overall_tenant_addr_rate, handover_hwaddr = self.best_handover_search(station, stats)
        else:
            overall_tenant_addr_rate, handover_hwaddr = self.rssi_handover_search(station, stats)

        if handover_hwaddr == attached_hwaddr:
            print("NO HANDOVER NEEDED")
            print("Handover hwaddr %s, attached_hwaddr %s" %(handover_hwaddr, attached_hwaddr))
            return

        print("BETTER HANDOVER FOUND")
        print("The overall rate of this tenant-address would be", overall_tenant_addr_rate)
        print("The handover must be performed from the AP %s to the AP %s" %(attached_hwaddr, handover_hwaddr))

        # The old wtp must delete the lvap (forcing the desconnection) and a new one is created in the new wtp (block)       
        for wtp in self.wtps():
            for block in wtp.supports:
                if block.hwaddr == handover_hwaddr:
                    wtp.connection.send_del_lvap(lvap)
                    lvap.downlink = block
                    lvap.authentication_state = False
                    lvap.association_state = False
                    lvap._assoc_id = 0
                    break

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == EtherAddress(station):
                entry.rssi = stats[EtherAddress(handover_hwaddr)]['rssi']
                entry.attached_hwaddr = handover_hwaddr
                break

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
    def rssi_stabilizing_period(self):
        """Return current rssi stabilizing periodd."""
        return self.__rssi_stabilizing_period

    @rssi_stabilizing_period.setter
    def rssi_stabilizing_period(self, rssi_stabilizing_period):
        self.__rssi_stabilizing_period = rssi_stabilizing_period

    @property
    def period(self):
        """Return current multicast DMS - Legacy period."""
        return self.__period

    @period.setter
    def period(self, period):
        self.__period = period


    def txp_bin_counter_callback(self, counter):
        """Counters callback."""

        self.log.info("Mcast address %s packets %u", counter.mcast,
                      counter.tx_packets[0])

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == counter.block.hwaddr:
                if counter.mcast in entry.last_txp_bin_counter:
                    entry.last_rx_pkts[counter.mcast] = counter.tx_packets[0] - entry.last_txp_bin_counter[counter.mcast]
                else:
                    entry.last_rx_pkts[counter.mcast] = counter.tx_packets[0]
                entry.last_txp_bin_counter[counter.mcast] = counter.tx_packets[0]
                break


    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""
        for block in wtp.supports:
            if any(entry.block.hwaddr == block.hwaddr for entry in self.mcast_wtps):
                continue

            wtp_info = MCastWTPInfo()
            wtp_info.block = block
            wtp_info.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB
            self.mcast_wtps.append(wtp_info)

            self.txp_bin_counter(block=block,
                mcast=self.mcast_addr,
                callback=self.txp_bin_counter_callback)


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


    def multicast_rate(self, hwaddr, old_client, new_client):
        min_rate = sys.maxsize
        min_highest_cur_prob_rate = sys.maxsize
        thershold_intersection_list = []
        thershold_highest_cur_prob_rate_intersection_list = []
        highest_thershold_valid = True
        second_thershold_valid = True
        old_client_rate = None
        old_client_highest_cur_prob_rate = None


        for index, entry in enumerate(self.mcast_clients):
            if entry.attached_hwaddr != hwaddr and (new_client is None or entry.addr != new_client):
                continue

            if old_client is not None and entry.addr == old_client:
                old_client_rate = entry.highest_rate
                old_client_highest_cur_prob_rate = entry.highest_cur_prob_rate
            else:
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
            if entry.last_rssi_change is not None and (time.time() - entry.last_rssi_change > self.rssi_stabilizing_period):
                entry.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB

            calculated_rate, highest_cur_prob_rate, thershold_intersection_list, thershold_highest_cur_prob_rate_intersection_list = self.multicast_rate(entry.block.hwaddr, None, None)
            
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


    def handover_rate_compute(self, hwaddr, old_client, new_client):

        calculated_rate, highest_cur_prob_rate, thershold_intersection_list, thershold_highest_cur_prob_rate_intersection_list = self.multicast_rate(hwaddr, old_client, new_client)
        
        # If some rates have been obtained as a result of the intersection, the highest one is selected as the rate.
        # Otherwise, the rate selected is the minimum among the MRs 
        if thershold_intersection_list:
            best_rate = max(thershold_intersection_list)
        else:
            best_rate = calculated_rate
        # The same happens for the cur prob. 
        if thershold_highest_cur_prob_rate_intersection_list:
            best_highest_cur_prob_rate = max(thershold_highest_cur_prob_rate_intersection_list)
        else:
            best_highest_cur_prob_rate = highest_cur_prob_rate

        return best_rate, highest_cur_prob_rate


    def rx_pkts_matching(self, attached_wtp_rx_pkts, hwaddr, wtp_index):
        lowest_value = sys.maxsize
        highest_value = 0
        lowest_sta = None 
        highest_sta = None

        for index, entry in enumerate(self.mcast_clients):
            if entry.attached_hwaddr == hwaddr:
                if entry.rx_pkts[self.mcast_addr] < lowest_value:
                    lowest_value = entry.rx_pkts[self.mcast_addr]
                    lowest_sta = entry.addr
                if entry.rx_pkts[self.mcast_addr] > highest_value:
                    highest_value = entry.rx_pkts[self.mcast_addr]
                    highest_sta = entry.addr

        minimum_required_pkts = 0.90 * attached_wtp_rx_pkts
        # If even the best receptor does not receive the required amount of packets,
        # it is necessary to decrease the rate
        print("WTP PACKETS %d CLIENT PACKETS %d" %(attached_wtp_rx_pkts, highest_value))
        if minimum_required_pkts > highest_value:
            self.mcast_wtps[wtp_index].prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
        else:
            self.mcast_wtps[wtp_index].prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB


    def overall_rate_calculation(self, aps_info, dst_addr):
        overall_tenant_rate = 0

        for key, value in aps_info.items():
            for index, entry in enumerate(self.mcast_wtps):
                if key == entry.block.hwaddr:
                    if entry.attached_clients > 0:
                        if entry.prob_measurement[dst_addr] == MCAST_EWMA_PROB:
                            overall_tenant_rate = overall_tenant_rate + entry.rate[dst_addr]
                        elif entry.prob_measurement[dst_addr] == MCAST_CUR_PROB:
                            overall_tenant_rate = overall_tenant_rate + entry.highest_cur_prob_rate[dst_addr]
                        break

        return overall_tenant_rate


    def handover_overall_rate_calculation(self, aps_info, dst_addr, evaluated_hwaddr, new_wtp_highest_cur_prob_rate, wtp_addr, old_wtp_new_rate):
        future_overall_tenant_rate = 0

        for key, value in aps_info.items():
            for index, entry in enumerate(self.mcast_wtps):
                if key == evaluated_hwaddr and key in aps_info:
                    future_overall_tenant_rate = future_overall_tenant_rate + new_wtp_highest_cur_prob_rate
                elif key == wtp_addr:
                    future_overal_tenant_rate = future_overall_tenant_rate + old_wtp_new_rate
                elif key == entry.block.hwaddr and key in aps_info:
                    if entry.attached_clients > 0:
                        if entry.prob_measurement[dst_addr] == MCAST_EWMA_PROB:
                            future_overall_tenant_rate = future_overall_tenant_rate + entry.rate[dst_addr]
                        elif entry.prob_measurement[dst_addr] == MCAST_CUR_PROB:
                            future_overall_tenant_rate = future_overall_tenant_rate + entry.cur_prob_rate[dst_addr]
                        break

        return future_overall_tenant_rate


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


    def best_handover_search(self, station, stats):
        evaluated_lvap = RUNTIME.lvaps[EtherAddress(station)]
        wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_wtp_rate_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_rssi = 0
        best_rate = 6
        new_wtps_possible_rates = dict()
        new_wtps_old_rates = dict()
        new_overall_tenant_addr_rate = dict()
        old_wtp_old_rate = None


        # The CURRENT PROB should be taken into account. It's a quick change
        # "old" wtp rate. 
        old_wtp_new_rate, old_wtp_new_highest_cur_prob_rate = self.handover_rate_compute(wtp_addr, station.upper(), None)
        if old_wtp_new_rate is None or old_wtp_new_highest_cur_prob_rate is None:
            return

        # "new" wtp rate
        # check the possible rate in all the wtps
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr in stats and entry.block.hwaddr != wtp_addr:
                new_wtp_best_rate, new_wtp_highest_cur_prob_rate = self.handover_rate_compute(entry.block.hwaddr, None, station.upper())
                new_wtps_possible_rates[entry.block.hwaddr] = new_wtp_highest_cur_prob_rate
                new_overall_tenant_addr_rate[entry.block.hwaddr] = self.handover_overall_rate_calculation(stats, self.mcast_addr, entry.block.hwaddr, new_wtp_highest_cur_prob_rate, wtp_addr, old_wtp_new_rate)

                if entry.prob_measurement == MCAST_EWMA_PROB:
                    new_wtps_old_rates[entry.block.hwaddr] = entry.rate[self.mcast_addr]
                elif entry.prob_measurement == MCAST_CUR_PROB:
                    new_wtps_old_rates[entry.block.hwaddr] = entry.cur_prob_rate[self.mcast_addr]
            elif entry.block.addr == wtp_addr:
                if entry.prob_measurement == MCAST_EWMA_PROB:
                    old_wtp_old_rate = entry.rate[self.mcast_addr]
                elif entry.prob_measurement == MCAST_CUR_PROB:
                    old_wtp_old_rate = entry.rate[self.mcast_addr]

        old_overall_tenant_addr_rate = self.overall_rate_calculation(stats, self.mcast_addr)

        # Tradeoff between the rates. 
        best_overall_tenant_addr_rate = old_overall_tenant_addr_rate
        best_overall_tenant_addr_hwaddr = wtp_addr

        for key, value in new_overall_tenant_addr_rate.items():
            # If the new global value is worse than the previous one, the handover to this ap is not worthy
            if value > best_overall_tenant_addr_rate:
                best_overall_tenant_addr_rate = value
                best_overall_tenant_addr_hwaddr = key
            elif value == best_overall_tenant_addr_rate:
                new_ap_difference = new_wtps_possible_rates[key] - new_wtps_old_rates[key]
                current_best_ap_difference = new_wtps_possible_rates[best_overall_tenant_addr_hwaddr] - new_wtps_old_rates[best_overall_tenant_addr_hwaddr]
                if new_ap_difference > current_best_ap_difference:
                    best_overall_tenant_addr_rate = value
                    best_overall_tenant_addr_hwaddr = key

        if best_overall_tenant_addr_hwaddr != wtp_addr:
            print("Old WTP rate without the client")
            print("Highest rate", old_wtp_new_rate)
            print("Second rate", old_wtp_new_highest_cur_prob_rate)

            print("New rates of the remaining APs if the client is moved there")
            for key, value in new_wtps_possible_rates.items():
                print(key)
                print(value)

            print("Overall rate before the handover")
            print(old_overall_tenant_addr_rate)

            print("Overall rate of the remaining APs if the client is moved there")
            for key, value in new_overall_tenant_addr_rate.items():
                print(key)
                print(value)

        return best_overall_tenant_addr_rate, best_overall_tenant_addr_hwaddr


    def rssi_handover_search(self, station, stats):
        evaluated_lvap = RUNTIME.lvaps[EtherAddress(station)]
        wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_rssi = stats[wtp_addr]['rssi']
        best_rate = stats[wtp_addr]['rate']

         # It checks if any wtp offers a better RSSI than the one is currently attached
        for key, value in stats.items():
            if value['rssi'] > best_rssi and key != best_wtp_addr:
                best_rssi = value['rssi']
                best_wtp_addr = key
                best_rate = value['rate']

        return best_rate, best_wtp_addr


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
                                    


def launch(tenant_id, every=DEFAULT_PERIOD, rssi={}, rx_pkts={}, aps={}, mcast_clients=[], mcast_wtps=[]):
    """ Initialize the module. """

    return MCast(tenant_id=tenant_id, every=every, rssi=rssi, rx_pkts=rx_pkts, aps=aps, mcast_clients=mcast_clients, mcast_wtps=mcast_wtps)
