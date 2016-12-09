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

import empower.logger
LOG = empower.logger.get_logger()

MCAST_EWMA_PROB = "ewma"
MCAST_CUR_PROB = "cur_prob"


class MCastMobilityManager(EmpowerApp):


    """Mobility manager app with multicast rate adaptation support.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        (old) ./empower-runtime.py apps.mcast.mcast:52313ecb-9d00-4b7d-b873-b55d3d9ada26
        (new) ./empower-runtime.py apps.mcast.mcastrssi --tenant_id=be3f8868-8445-4586-bc3a-3fe5d2c17339

    """

    def __init__(self, **kwargs):

        EmpowerApp.__init__(self, **kwargs)

        self.__rx_pkts = {} # {client:pkts, client:pkts...}
        self.__aps = {} # {client: {ap:rssi, ap:rssi...}, client: {ap:rssi, ap:rssi...}...}
        self.__mcast_clients = []
        self.__mcast_wtps = [] 
        self.__prob_thershold = 95
        self.__rssi_stabilizing_period = 5
        self.__handover_clients = {}
        self.__handover_occupancies = {}
        self.__rssi_thershold = -65
        self.__mcast_addr = EtherAddress("01:00:5e:00:00:fb")
        self.__minimum_rssi_difference = 10
        self.__occupancy_rate = 0

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)
        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)
        self.wtpdown(callback=self.wtp_down_callback)


    @property
    def rx_pkts(self):
        """Return loop period."""
        return self.__rx_pkts

    @rx_pkts.setter
    def rx_pkts(self, rx_pkts_info):
        """Updates the rate according to the rx_pkts received"""
        station = EtherAddress(rx_pkts_info['addr'])
        if not rx_pkts_info or not station in RUNTIME.lvaps:
            return

        attached_wtp_tx_pkts = 0
        stats = rx_pkts_info['stats']
        lvap = RUNTIME.lvaps[station]
        hwaddr = next(iter(lvap.downlink.keys())).hwaddr
        wtp_ix = -1

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == hwaddr:
                attached_wtp_tx_pkts = entry.last_tx_pkts
                wtp_ix = index
                break

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                for key, value in stats.items():
                    entry.rx_pkts[EtherAddress(key)] = value
                # It maches the received packets agains the amount of them sent by the WTP to a given multicast address
                self.rx_pkts_matching(attached_wtp_tx_pkts, hwaddr, wtp_ix)
                self.__rx_pkts[station] = stats
                break

    @property
    def aps(self):
        """Return loop period."""
        return self.__aps

    @aps.setter
    def aps(self, aps_info):
        """Updates the rate according to the aps information received"""
        station = EtherAddress(aps_info['addr'])

        if not aps_info or station not in RUNTIME.lvaps:
            return

        lvap = RUNTIME.lvaps[station]
        stats = self.lvap_bssid_to_hwaddr(aps_info['wtps'])
        disable_old_wtp = False
        attached_hwaddr = (next(iter(lvap.downlink))).hwaddr
        enable_handover_search = False
        max_rate = None

        if self.occupancy_rate == 0:
            self.occupancy_rate = self.overall_occupancy_rate_calculation(lvap.ssid)

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr not in stats:
                continue
            if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                if self.mcast_addr in entry.rate:
                    stats[entry.block.hwaddr]['rate'] = entry.rate[self.mcast_addr]
                else:
                    stats[entry.block.hwaddr]['rate'] = 0
            elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                if self.mcast_addr in entry.cur_prob_rate:
                    stats[entry.block.hwaddr]['rate'] = entry.cur_prob_rate[self.mcast_addr]
                else:
                    stats[entry.block.hwaddr]['rate'] = 0

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                for key, value in stats.items():
                    if key not in entry.wtps or (key in entry.wtps and entry.wtps[key] != value):
                        enable_handover_search = True
                    entry.wtps[key] = value
                if entry.last_handover_time is not None and time.time() - entry.last_handover_time <= 3:
                    enable_handover_search = False
                # Remove the APs that are not already in the coverage area of this client
                useless_wtps = []
                for key, value in entry.wtps.items():
                    if key not in stats:
                        useless_wtps.append(key)
                for i, wtp in enumerate(useless_wtps):
                    del entry.wtps[wtp]

                entry.rssi = entry.wtps[attached_hwaddr]['rssi']
                self.__aps[station] = stats
                max_rate = max(int(float(key)) for key in entry.rates.keys())
                break

        # Check if the transmission will be turned off in the current WTP (0 clients)
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == attached_hwaddr:
                entry.attached_clients_rssi[station] = stats[attached_hwaddr]['rssi']
                entry.attached_clients = len(entry.attached_clients_rssi)
                rssi_values = list(entry.attached_clients_rssi.values())
                if len(list(filter((0).__ne__, rssi_values))) > 0:
                    entry.avg_perceived_rssi =  statistics.mean(list(filter((0).__ne__, rssi_values)))
                if entry.attached_clients > 1 and len(list(filter((0).__ne__, rssi_values))) > 1:
                    entry.dev_perceived_rssi = statistics.stdev(list(filter((0).__ne__, rssi_values)))
                else:
                    entry.dev_perceived_rssi = 0

                entry.last_rssi_change = time.time()
                entry.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
                if entry.attached_clients == 1:
                    disable_old_wtp = True
                elif entry.attached_clients == 1 and entry.cur_prob_rate[self.mcast_addr] == max_rate and stats[attached_hwaddr]['rssi'] >= self.rssi_thershold:
                    enable_handover_search = False
                break

        for key, value in self.handover_occupancies.items():
            if value['handover_client'] == station:
                enable_handover_search = False
                break

        # If there is only one AP is not worthy to do the process
        if len(stats) <= 1 or enable_handover_search is False:
            return

        self.handover_search(station, stats, disable_old_wtp)


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
    def handover_clients(self):
        """Return current status of the clients that are performing a handover."""
        return self.__handover_clients

    @handover_clients.setter
    def handover_clients(self, handover_clients):
        self.__handover_clients = handover_clients

    @property
    def handover_occupancies(self):
        """Return the occupancy rate of the network before a given handover."""
        return self.__handover_occupancies

    @handover_occupancies.setter
    def handover_occupancies(self, handover_occupancies):
        self.__handover_occupancies = handover_occupancies

    @property
    def rssi_thershold(self):
        """Return the minimum required rssi level to perform a handover."""
        return self.__rssi_thershold

    @rssi_thershold.setter
    def rssi_thershold(self, rssi_thershold):
        self.__rssi_thershold = rssi_thershold

    @property
    def mcast_addr(self):
        """Return mcast_addr used."""
        return self.__mcast_addr

    @mcast_addr.setter
    def mcast_addr(self, mcast_addr):
        self.__mcast_addr = mcast_addr

    @property
    def occupancy_rate(self):
        """Return the global occupancy rate for the current tenant."""
        return self.__occupancy_rate

    @occupancy_rate.setter
    def occupancy_rate(self, occupancy_rate):
        self.__occupancy_rate = occupancy_rate

    def txp_bin_counter_callback(self, counter):
        """Counters callback."""

        self.log.info("Mcast address %s packets %u bytes %u", counter.mcast,
                      counter.tx_packets[0], counter.tx_bytes[0])

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == counter.block.hwaddr:
                if counter.mcast in entry.last_txp_bin_tx_pkts_counter:
                    entry.last_tx_pkts[counter.mcast] = counter.tx_packets[0] - entry.last_txp_bin_tx_pkts_counter[counter.mcast]
                else:
                    entry.last_tx_pkts[counter.mcast] = counter.tx_packets[0]
                entry.last_txp_bin_tx_pkts_counter[counter.mcast] = counter.tx_packets[0]
                if counter.mcast in entry.last_txp_bin_tx_bytes_counter:
                    entry.last_tx_bytes[counter.mcast] = counter.tx_bytes[0] - entry.last_txp_bin_tx_bytes_counter[counter.mcast]
                else:
                    entry.last_tx_bytes[counter.mcast] = counter.tx_bytes[0]
                entry.last_txp_bin_tx_bytes_counter[counter.mcast] = counter.tx_bytes[0]
                break


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

            self.txp_bin_counter(block=block,
                mcast=self.mcast_addr,
                callback=self.txp_bin_counter_callback,
                every=1000)


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
        current_rssi = 0

        # If this lvap is created due to a handover, its information must be restored
        if lvap.addr in self.handover_clients:
            lvap_info = self.handover_clients[lvap.addr]
            del self.handover_clients[lvap_info.addr]

        lvap_info.addr = lvap.addr
        lvap_info.attached_hwaddr = default_block.hwaddr
        if default_block.hwaddr in lvap_info.wtps:
            current_rssi = lvap_info.wtps[default_block.hwaddr]['rssi']
        self.mcast_clients.append(lvap_info)

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == default_block.hwaddr:
                entry.attached_clients_rssi [lvap.addr] = current_rssi
                entry.attached_clients = len(entry.attached_clients_rssi)
                rssi_values = list(entry.attached_clients_rssi.values())
                if len(list(filter((0).__ne__, rssi_values))) > 0:
                    entry.avg_perceived_rssi =  statistics.mean(list(filter((0).__ne__, rssi_values)))
                if entry.attached_clients > 1 and len(list(filter((0).__ne__, rssi_values))) > 1:
                    entry.dev_perceived_rssi = statistics.stdev(list(filter((0).__ne__, rssi_values)))
                else:
                    entry.dev_perceived_rssi = 0
                if self.mcast_addr in entry.last_tx_pkts and self.mcast_addr in entry.rate:
                    self.occupancy_rate = self.overall_occupancy_rate_calculation(lvap.ssid)
                break

    def lvap_leave_callback(self, lvap):
        """Called when an LVAP disassociates from a tennant."""

        default_block = next(iter(lvap.downlink))
        handover = False

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == lvap.addr:
                del self.mcast_clients[index]
                if time.time() - entry.last_handover_time <= 3:
                    handover = True
                break

        for key, value in self.handover_occupancies.items():
            if value['handover_client'] == lvap.addr:
                handover = True
                break

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == default_block.hwaddr:
                if lvap.addr in entry.attached_clients_rssi and handover is False:  
                    del entry.attached_clients_rssi[lvap.addr]
                    entry.attached_clients = len(entry.attached_clients_rssi)
                    rssi_values = list(entry.attached_clients_rssi.values())
                    if len(list(filter((0).__ne__, rssi_values))) > 0:
                        entry.avg_perceived_rssi =  statistics.mean(list(filter((0).__ne__, rssi_values)))
                    if entry.attached_clients > 1 and len(list(filter((0).__ne__, rssi_values))) > 1:
                        entry.dev_perceived_rssi = statistics.stdev(list(filter((0).__ne__, rssi_values)))
                    else:
                        entry.dev_perceived_rssi = 0
                break

        # In case this was the worst receptor, the date rate for legacy multicast must be recomputed
        if self.mcast_clients:
            self.legacy_mcast_compute()


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
            # If a handover has been recently performed. Let's evaluate the new occupancy rate. 
            if self.handover_occupancies:
                handover_checked = []
                previous_rssi = 0

                for key, value in self.handover_occupancies.items():
                    # Wait some time to get statistics before checking if the handover was valid
                    if time.time() - value['handover_time'] < 1:
                        continue

                    handover_occupancy_rate = self.overall_occupancy_rate_calculation(value['tenant_name'])
                    handover_checked.append(key)

                    for index, entry in enumerate(self.mcast_clients):
                        if value['handover_client'] == entry.addr:
                            previous_rssi = entry.wtps[key]['rssi']
                            break

                    # If the previous occupancy rate was better, the handover must be reverted
                    if value['previous_occupancy'] < handover_occupancy_rate and previous_rssi > self.rssi_thershold:
                        self.log.info("The handover from the AP %s to the AP %s for the client %s IS NOT efficient. The previous channel occupancy rate was %d(ms) and it is %d(ms) after the handover. It is going to be reverted", \
                                key, value['handover_ap'], value['handover_client'], value['previous_occupancy'], handover_occupancy_rate)
                        self.revert_handover(value['handover_client'], key, value['handover_ap'])
                    elif value['previous_occupancy'] < handover_occupancy_rate and previous_rssi < self.rssi_thershold:
                        self.log.info("The handover from the AP %s to the AP %s for the client %s is efficient to IMPROVE SIGNAL STRENGHT. The previous channel occupancy rate was %d(ms) and it is %d(ms) after the handover \
                        But the previous RSSI %d db was below the defined thereshold %d db", \
                         key, value['handover_ap'], value['handover_client'], value['previous_occupancy'], handover_occupancy_rate, previous_rssi, self.rssi_thershold)    
                    elif value['previous_occupancy'] > handover_occupancy_rate:
                        self.log.info("The handover from the AP %s to the AP %s for the client %s is efficient. The previous channel occupancy rate was %d(ms) and it is %d(ms) after the handover", \
                         key, value['handover_ap'], value['handover_client'], value['previous_occupancy'], handover_occupancy_rate)                 

                for index, entry in enumerate(handover_checked):
                    del self.handover_occupancies[entry]

            for index, entry in enumerate(self.mcast_wtps):
                if entry.last_prob_update == 0:
                    entry.last_prob_update = time.time()

                tx_policy = entry.block.tx_policies[self.mcast_addr] 

                # If there is no clients, the default mode is DMS
                if entry.attached_clients == 0:
                    entry.mode = TX_MCAST_DMS_H
                    tx_policy.mcast = TX_MCAST_DMS
                # If there is only one client attached to this AP, the information is sent in DMS mode
                # The rate is also calculated.
                # elif entry.attached_clients == 1:
                #     ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
                #     entry.rate[self.mcast_addr] = ewma_rate
                #     entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
                #     entry.mode = TX_MCAST_DMS_H
                #     tx_policy.mcast = TX_MCAST_DMS
                else: 
                    # If there are many clients per AP, it combines DMS and legacy to obtain statistics. 
                    # If the AP is in DMS mode and the has been an update of the RSSI, the mode is changed to legacy.
                    if entry.mode == TX_MCAST_DMS_H and entry.last_rssi_change > 0 and time.time() - entry.last_rssi_change < entry.legacy_max_period:
                        entry.mode = TX_MCAST_LEGACY_H
                        if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                            tx_policy.mcs = [int(entry.rate[self.mcast_addr])]
                        elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                            tx_policy.mcs = [int(entry.cur_prob_rate[self.mcast_addr])]
                    # If the AP is in legacy mode and it is a long period since the last statistics update, the mode is changed to DMS.
                    elif entry.mode == TX_MCAST_LEGACY_H and (time.time() - entry.last_prob_update > entry.legacy_max_period):
                        entry.last_prob_update = time.time()
                        tx_policy.mcast = TX_MCAST_DMS
                        entry.mode = TX_MCAST_DMS_H
                    # If there are enough statistics, the retransmission mode is changed to legacy and the rate is calculated taken them as a basis. 
                    elif entry.mode == TX_MCAST_DMS_H and (time.time() - entry.last_prob_update > entry.dms_max_period):      
                        ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
                        tx_policy.mcast = TX_MCAST_LEGACY
                        if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                            tx_policy.mcs = [int(ewma_rate)]
                        elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                            tx_policy.mcs = [int(cur_prob_rate)]
                        entry.rate[self.mcast_addr] = ewma_rate
                        entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
                        entry.last_prob_update = time.time()
                        entry.mode = TX_MCAST_LEGACY_H


    def calculate_wtp_rate(self, mcast_wtp):
        if  mcast_wtp.last_rssi_change > 0 and (time.time() - mcast_wtp.last_rssi_change < self.rssi_stabilizing_period):
            mcast_wtp.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
        else:
            mcast_wtp.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB

        calculated_rate, highest_cur_prob_rate, thershold_intersection_list, thershold_highest_cur_prob_rate_intersection_list = self.multicast_rate(mcast_wtp.block.hwaddr)
        
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

        return best_rate, best_highest_cur_prob_rate


    def multicast_rate(self, hwaddr):
        min_rate = sys.maxsize
        min_highest_cur_prob_rate = sys.maxsize
        thershold_intersection_list = []
        thershold_highest_cur_prob_rate_intersection_list = []
        highest_thershold_valid = True
        second_thershold_valid = True

        for index, entry in enumerate(self.mcast_clients):
            if entry.attached_hwaddr == hwaddr:
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
                if entry.block.hwaddr == hwaddr:
                    min_rate = min(entry.block.supports)
                    min_highest_cur_prob_rate = min(entry.block.supports)
                    break

        return min_rate, min_highest_cur_prob_rate, thershold_intersection_list, thershold_highest_cur_prob_rate_intersection_list


    def legacy_mcast_compute(self):
        for index, entry in enumerate(self.mcast_wtps):
            if entry.attached_clients == 0:
                continue

            # It obtains the most appropiate rate
            if entry.last_rssi_change > 0 and (time.time() - entry.last_rssi_change > self.rssi_stabilizing_period):
                entry.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB
            elif entry.last_rssi_change > 0 and (time.time() - entry.last_rssi_change < self.rssi_stabilizing_period):
                entry.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB

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

            tx_policy = entry.block.tx_policies[self.mcast_addr]
            tx_policy.mcast = TX_MCAST_LEGACY

            # The rate is selected according to the probability used in that moment. 
            if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                tx_policy.mcs = [int(best_rate)]
            elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                tx_policy.mcs = [int(best_highest_cur_prob_rate)]


    def rx_pkts_matching(self, attached_wtp_tx_pkts, hwaddr, wtp_index):
        lowest_value = sys.maxsize
        highest_value = 0
        lowest_sta = None 
        highest_sta = None

        for index, entry in enumerate(self.mcast_clients):
            if entry.attached_hwaddr == hwaddr:
                if self.mcast_addr not in entry.rx_pkts:
                    continue
                if entry.rx_pkts[self.mcast_addr] < lowest_value:
                    lowest_value = entry.rx_pkts[self.mcast_addr]
                    lowest_sta = entry.addr
                if entry.rx_pkts[self.mcast_addr] > highest_value:
                    highest_value = entry.rx_pkts[self.mcast_addr]
                    highest_sta = entry.addr

        print("Best station. Highest value. Rx_pkts", highest_value)
        print("Worst station. Lowest value. Rx_pkts", lowest_value)
        print("Attached wtp rx_pkts", attached_wtp_tx_pkts[self.mcast_addr])

        minimum_required_pkts = 0.90 * attached_wtp_tx_pkts[self.mcast_addr]
        print("Minimum required pkts (90% quality)", minimum_required_pkts)

        # if minimum_required_pkts > highest_value:
        #     self.mcast_wtps[wtp_index].prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
        # else:
        #     self.mcast_wtps[wtp_index].prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB


    # Calculates the global occupancy rate for the current situation (without performing any handover)
    def overall_occupancy_rate_calculation(self, tenant_name):
        overall_tenant_occupancy = 0
        evaluated_hwaddr = []

        for tenant in RUNTIME.tenants.values():
            if tenant.tenant_name == tenant_name:
                for wtp_in_tenant in tenant.wtps.values():
                    for block in wtp_in_tenant.supports:
                        evaluated_hwaddr.append(block.hwaddr)
                break
       
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr not in evaluated_hwaddr:
                continue
            if entry.attached_clients > 0:
                if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                    overall_tenant_occupancy = overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[self.mcast_addr], entry.last_tx_bytes[self.mcast_addr], entry.rate[self.mcast_addr], entry.mode)
                elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                    overall_tenant_occupancy = overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[self.mcast_addr], entry.last_tx_bytes[self.mcast_addr], entry.cur_prob_rate[self.mcast_addr], entry.mode)

        return overall_tenant_occupancy


    def packet_transmission_time(self, last_tx_pkts, last_tx_bytes, rate, mode):
        avg_pkt_size = 0
        difs = 28
        sifs = 10
        phy_header_pclp_preamble_time = 16
        signal_extension_time = 6
        phy_header_pclp_header_bits = 24
        mac_ack_header_bits = 134
        transmission_time = 0


        if last_tx_pkts > 0:
            avg_pkt_size = float(last_tx_bytes / last_tx_pkts)
        else:
            avg_pkt_size = self.current_transmission_avg_pkt_size()

        if mode == TX_MCAST_DMS_H:
            transmission_time = float(difs + (avg_pkt_size * 8 + 2*phy_header_pclp_header_bits + mac_ack_header_bits) / rate + 2*phy_header_pclp_preamble_time + sifs)
        elif mode == TX_MCAST_LEGACY_H:
            transmission_time = float(difs + (avg_pkt_size * 8 + 2*phy_header_pclp_header_bits) / rate + 2*phy_header_pclp_preamble_time)

        return transmission_time
        

    def current_transmission_avg_pkt_size(self):
        avg_pkt_size = 1500
        pkts_counter = 0
        bytes_counter = 0

        for index, entry in enumerate(self.mcast_wtps):
            if entry.attached_clients > 0 and entry.last_tx_pkts[self.mcast_addr] > 0 and entry.last_tx_bytes[self.mcast_addr] > 0:
                pkts_counter = pkts_counter + entry.last_tx_pkts[self.mcast_addr]
                bytes_counter = bytes_counter + entry.last_tx_bytes[self.mcast_addr]

        if pkts_counter > 0 and bytes_counter > 0:
            avg_pkt_size = bytes_counter / pkts_counter
        
        return avg_pkt_size


    def lvap_bssid_to_hwaddr(self, aps_info):
        aps_hwaddr_info = dict()
        shared_tenants = [x for x in RUNTIME.tenants.values()
                              if x.bssid_type == T_TYPE_SHARED]

        for key, value in aps_info.items():
            for tenant in shared_tenants:
                if EtherAddress(key) in tenant.vaps and tenant.vaps[EtherAddress(key)].block.hwaddr not in aps_hwaddr_info:
                    hwaddr = tenant.vaps[EtherAddress(key)].block.hwaddr
                    value['lvap_bssid'] = EtherAddress(key)
                    aps_hwaddr_info[hwaddr] = value

        return aps_hwaddr_info


    def handover_search(self, station, stats, disable_old_wtp):
        evaluated_lvap = RUNTIME.lvaps[station]
        wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        old_wtp_old_rate = stats[wtp_addr]['rate'] #TODO. Change for the one wtp
        best_wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_rssi = stats[wtp_addr]['rssi']
        possible_handover_wtps = {}
        possible_handover_empty_wtps = {}
        client_index = -1
        checking_rssi_rate_relation = True

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                client_index = index
                break

        # It checks if any wtp offers a better RSSI than the one is currently attached
        for key, value in stats.items():
            if key == wtp_addr:
                continue
            ################################# Previous handover checkers ################################# 
            if key in self.mcast_clients[client_index].last_unsuccessful_handover:
                self.mcast_clients[client_index].last_unsuccessful_handover[key]['handover_time'] = time.time()


                # If there is not significant changes in the RSSI perceived and the rate is the same than the last time, skip this AP.
                if (abs(abs(int(value['rssi'])) - abs(int(self.mcast_clients[client_index].last_unsuccessful_handover[key]['rssi']))) < self.__minimum_rssi_difference) and \
                self.mcast_clients[client_index].last_unsuccessful_handover[key]['rate'] == value['rate']:   
                    continue
                elif (abs(abs(int(value['rssi'])) - abs(int(self.mcast_clients[client_index].last_unsuccessful_handover[key]['rssi']))) > self.__minimum_rssi_difference) or \
                self.mcast_clients[client_index].last_unsuccessful_handover[key]['rate'] != value['rate']:
                    self.mcast_clients[client_index].last_unsuccessful_handover[key]['handover_retries'] = self.mcast_clients[client_index].last_unsuccessful_handover[key]['handover_retries'] + 1

                    if self.mcast_clients[client_index].last_unsuccessful_handover[key]['handover_retries'] <= self.rssi_stabilizing_period:
                        continue
                    else:
                        del self.mcast_clients[client_index].last_unsuccessful_handover[key]

            ################################# RSSI selection for handover ################################# 
            if value['rssi'] > self.rssi_thershold and int(value['rssi']) > int(stats[wtp_addr]['rssi']) and key != best_wtp_addr:
                possible_handover_wtps[key] = {'perceived_rssi': value['rssi'], 'current_rate': value['rate'], 'avg_rssi':0, 'dev_rssi':0}

                if value['rssi'] > best_rssi:
                    #(time.time() - self.mcast_clients[client_ix].last_unsuccessful_handover[key]) > 5):
                    best_rssi = value['rssi']
                    best_wtp_addr = key

        ################################# RSSI/Noise ratio evaluation for handover ################################# 
        # If the best AP does not have any clients, perhpas it's the best option?
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == best_wtp_addr:
                if entry.attached_clients == 0:
                    checking_rssi_rate_relation = False
                break


        if checking_rssi_rate_relation is True and possible_handover_wtps:
            for index, entry in enumerate(self.mcast_wtps):
                if possible_handover_wtps and entry.block.hwaddr in possible_handover_wtps:
                    if entry.attached_clients > 0:
                        possible_handover_wtps[entry.block.hwaddr]['avg_rssi'] = entry.avg_perceived_rssi
                        possible_handover_wtps[entry.block.hwaddr]['dev_rssi'] = entry.dev_perceived_rssi
                    else:
                        possible_handover_empty_wtps[entry.block.hwaddr] = value['perceived_rssi']
                        del possible_handover_wtps[entry.block.hwaddr]

            best_wtp_addr, best_values = possible_handover_wtps.popitem()
            for key, value in possible_handover_wtps.items():
                # They could experience the same noise level. Calculate it and compare with the rssi perceived by the client
                if value['current_rate'] < best_values['current_rate'] and value['avg_rssi'] < best_values['avg_rssi']:
                    evaluated_ratio = float(value['current_rate'] / value['avg_rssi'])
                    current_ratio = float(best_values['current_rate'] / best_values['avg_rssi'])
                    # The AP has at least 2 clients
                    evaluated_similarity = False
                    if value['dev_rssi'] > 0:
                        evaluated_conf_interval = stats.norm.interval(0.95, loc=value['avg_rssi'], scale=value['dev_rssi'])
                        evaluated_similarity = value['perceived_rssi'] > evaluated_conf_interval[0] and value['perceived_rssi'] < evaluated_conf_interval[1]
                    # The AP has 1 client
                    else:
                        current_distance = abs(abs(value['avg_rssi']) - abs(value['perceived_rssi']))
                        evaluated_distance = abs(abs(best_values['avg_rssi']) - abs(best_values['perceived_rssi']))
                        evaluated_similarity = evaluated_distance < current_distance
                    # The evaluated AP has a lower noise level
                    if evaluated_ratio > current_ratio and evaluated_similarity is True:
                        best_wtp_addr = key
                        best_values = value
                # If the rate and the perceived RSSI is higher, the candidate for the best AP is changed
                elif value['current_rate'] > best_values['current_rate'] and value['avg_rssi'] > best_values['avg_rssi']:
                    best_wtp_addr = key
                    best_values = value

            # The best empty and non-empty APs are compared
            if possible_handover_empty_wtps:
                best_empty_wtp = max(possible_handover_empty_wtps, key=possible_handover_empty_wtps.get)
                best_empty_rssi = possible_handover_empty_wtps[best_empty_wtp]
                if best_values['perceived_rssi'] < best_empty_rssi:
                    best_wtp_addr = best_empty_wtp

        if best_wtp_addr == wtp_addr:
            self.log.info("NO HANDOVER NEEDED")
            return

        self.log.info("BETTER HANDOVER FOUND")

        #handover. It's necessary to save the old occupancy and AP
        self.handover_occupancies[wtp_addr] = {
                                                'handover_client': station,
                                                'handover_ap': best_wtp_addr,
                                                'previous_occupancy': self.overall_occupancy_rate_calculation(evaluated_lvap.ssid),
                                                'handover_time': time.time(), 
                                                'tenant_name': evaluated_lvap.ssid,
                                                }

        self.log.info("The handover is performed from the AP %s to the AP %s for the station %s", wtp_addr, best_wtp_addr, station)

        # A copy of the client data is stored and it is restored after the handover
        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                entry.rssi = stats[best_wtp_addr]['rssi']
                entry.attached_hwaddr = best_wtp_addr
                self.handover_clients[entry.addr] = entry
                entry.last_handover_time = time.time()
                break

        # The old wtp must delete the lvap (forcing the desconnection) and a new one is created in the new wtp (block) 
        # Force that AP to send in DMS to gather statistics. The new occupancy rate is checked in the next loop period      
        for wtp in self.wtps():
            for block in wtp.supports:
                if block.hwaddr == wtp_addr:
                    wtp.connection.send_del_lvap(evaluated_lvap)
                if block.hwaddr == best_wtp_addr:
                    tx_policy = block.tx_policies[self.mcast_addr] 
                    tx_policy.mcast = TX_MCAST_DMS
                    evaluated_lvap.scheduled_on = block
                    evaluated_lvap.lvap_bssid = stats[best_wtp_addr]['lvap_bssid']

        # Updates the client information in the corresponding APs
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == best_wtp_addr:
                tx_policy = entry.block.tx_policies[self.mcast_addr] 
                tx_policy.mcast = TX_MCAST_DMS
                entry.mode = TX_MCAST_DMS_H
                entry.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
                entry.last_prob_update = time.time()
                ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
                entry.rate[self.mcast_addr] = ewma_rate
                entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
            elif entry.block.hwaddr == wtp_addr:
                tx_policy = entry.block.tx_policies[self.mcast_addr] 
                if station in entry.attached_clients_rssi:
                    del entry.attached_clients_rssi[station] 
                    entry.attached_clients = len(entry.attached_clients_rssi)              
                    rssi_values = list(entry.attached_clients_rssi.values())
                    if len(list(filter((0).__ne__, rssi_values))) > 0:
                        entry.avg_perceived_rssi =  statistics.mean(list(filter((0).__ne__, rssi_values)))
                    else:
                        entry.avg_perceived_rssi = 0
                    if entry.attached_clients > 1 and len(list(filter((0).__ne__, rssi_values))) > 1:
                        entry.dev_perceived_rssi = statistics.stdev(list(filter((0).__ne__, rssi_values)))
                    else:
                        entry.dev_perceived_rssi = 0 
                ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
                if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                    tx_policy.mcs = [int(ewma_rate)]
                elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                    tx_policy.mcs = [int(cur_prob_rate)]
                entry.rate[self.mcast_addr] = ewma_rate
                entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
                entry.last_prob_update = time.time()


    def revert_handover(self, station, correct_wtp, wrong_wtp):
        evaluated_lvap = RUNTIME.lvaps[station]
        correct_lvap_bssid = None

                # Updates the client information in the corresponding APs
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == correct_wtp:
                tx_policy = entry.block.tx_policies[self.mcast_addr] 
                tx_policy.mcast = TX_MCAST_DMS
                entry.mode = TX_MCAST_DMS_H
                entry.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
                entry.last_prob_update = time.time()
                ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
                entry.rate[self.mcast_addr] = ewma_rate
                entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
                self.calculate_wtp_rate(entry)
            elif entry.block.hwaddr == wrong_wtp:
                tx_policy = entry.block.tx_policies[self.mcast_addr] 
                if station in entry.attached_clients_rssi:
                    del entry.attached_clients_rssi[station]
                    entry.attached_clients = len(entry.attached_clients_rssi)               
                    rssi_values = list(entry.attached_clients_rssi.values())
                    if len(list(filter((0).__ne__, rssi_values))) > 0:
                        entry.avg_perceived_rssi =  statistics.mean(list(filter((0).__ne__, rssi_values)))
                    else:
                        entry.avg_perceived_rssi = 0
                    if entry.attached_clients > 1 and len(list(filter((0).__ne__, rssi_values))) > 1:
                        entry.dev_perceived_rssi = statistics.stdev(list(filter((0).__ne__, rssi_values)))
                ewma_rate, cur_prob_rate = self.calculate_wtp_rate(entry)
                if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                    tx_policy.mcs = [int(ewma_rate)]
                elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                    tx_policy.mcs = [int(cur_prob_rate)]
                entry.rate[self.mcast_addr] = ewma_rate
                entry.cur_prob_rate[self.mcast_addr] = cur_prob_rate
                entry.last_prob_update = time.time()
                tx_pkts = entry.last_tx_pkts[self.mcast_addr]
                nb_clients = entry.attached_clients

        # A copy of the client data is stored and it is restored after the handover
        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                entry.last_unsuccessful_handover[wrong_wtp] = {
                                                            'rssi': entry.wtps[wrong_wtp]['rssi'],
                                                            'rate': entry.wtps[wrong_wtp]['rate'],
                                                            'tx_pkts': tx_pkts,
                                                            'nb_clients': nb_clients,
                                                            'handover_time': time.time(),
                                                            'handover_retries': 0
                                                            }

                entry.rssi = entry.wtps[correct_wtp]['rssi']
                entry.attached_hwaddr = correct_wtp
                correct_lvap_bssid = entry.wtps[correct_wtp]['lvap_bssid']
                self.handover_clients[entry.addr] = entry
                break

        # The old wtp must delete the lvap (forcing the desconnection) and a new one is created in the new wtp (block) 
        # Force that AP to send in DMS to gather statistics. The new occupancy rate is checked in the next loop period      
        for wtp in self.wtps():
            for block in wtp.supports:
                if block.hwaddr == wrong_wtp:
                    wtp.connection.send_del_lvap(evaluated_lvap)
                elif block.hwaddr == correct_wtp:
                    tx_policy = block.tx_policies[self.mcast_addr] 
                    tx_policy.mcast = TX_MCAST_DMS
                    evaluated_lvap.scheduled_on = block
                    evaluated_lvap.lvap_bssid = correct_lvap_bssid


    def attached_clients(self):
        nb_attached_clients = 0

        for index, entry in enumerate(self.mcast_wtps):
            nb_attached_clients = nb_attached_clients + entry.attached_clients

        return nb_attached_clients
    

    def to_dict(self):
        """Return JSON-serializable representation of the object."""
        out = super().to_dict()
        handover_occupancies = {str(k): v for k, v in self.handover_occupancies.items()}

        out['mcast_clients'] = []
        for p in self.mcast_clients:
            out['mcast_clients'].append(p.to_dict())
        out['mcast_wtps'] = []
        for p in self.mcast_wtps:
            out['mcast_wtps'].append(p.to_dict())
        out['mcast_addr'] = self.mcast_addr
        out['rssi_thershold'] = self.rssi_thershold
        out['handover_occupancies'] = handover_occupancies
        out['occupancy_rate (microsec)'] = self.occupancy_rate

        return out
                                    


def launch(tenant_id, every=1000, rx_pkts={}, aps={}, mcast_clients=[], mcast_wtps=[]):
    """ Initialize the module. """

    return MCastMobilityManager(tenant_id=tenant_id, every=every, rx_pkts=rx_pkts, aps=aps, mcast_clients=mcast_clients, mcast_wtps=mcast_wtps)
