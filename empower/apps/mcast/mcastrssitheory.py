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

        self.__rssi = {} # {client:rssi, client:rssi...}
        self.__rx_pkts = {} # {client:pkts, client:pkts...}
        self.__aps = {} # {client: {ap:rssi, ap:rssi...}, client: {ap:rssi, ap:rssi...}...}
        self.__mcast_clients = []
        self.__mcast_wtps = [] 
        self.__prob_thershold = 95
        self.__rssi_stabilizing_period = 5
        self.__handover_clients = {}
        self.__rssi_thershold = -65
        self.__mcast_addr = EtherAddress("01:00:5e:00:00:fb")

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)
        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)
        self.wtpdown(callback=self.wtp_down_callback)


    @property
    def rssi(self):
        """Return loop period."""
        return self.__rssi

    @rssi.setter
    def rssi(self, rssi_info):
        """Updates the rate according to the rssi"""

        if not rssi_info:
            return

        station = EtherAddress(rssi_info['addr'])
        if not station in RUNTIME.lvaps:
            return
       
        lvap = RUNTIME.lvaps[station]
        hwaddr = next(iter(lvap.downlink.keys())).hwaddr

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
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


    @property
    def rx_pkts(self):
        """Return loop period."""
        return self.__rx_pkts

    @rx_pkts.setter
    def rx_pkts(self, rx_pkts_info):
        """Updates the rate according to the rx_pkts received"""

        if not rx_pkts_info:
            return

        station = EtherAddress(rx_pkts_info['addr'])
        if not station in RUNTIME.lvaps:
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
                # It maches the received packets agains the amount of them sent by the WTP 
                # to a given multicast address
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
        if not aps_info:
            return

        station = EtherAddress(aps_info['addr'])
        attached_hwaddr = None

        if station not in RUNTIME.lvaps:
            return

        lvap = RUNTIME.lvaps[station]
        stats = self.lvap_bssid_to_hwaddr(aps_info['wtps'])
        nb_clients = self.attached_clients()
        client_ix = -1
        disable_old_wtp = False

        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                for key, value in stats.items():
                    entry.wtps[EtherAddress(key)] = value
                attached_hwaddr = entry.attached_hwaddr
                client_ix = index
                self.__aps[station] = stats
                break

        # If there is only one AP is not worthy to do the process
        if len(stats) == 1:
            return

        # Check if the transmission will be turned off in the current WTP (0 clients)
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == attached_hwaddr:
                if entry.attached_clients == 1:
                    disable_old_wtp = True
                    break

        # If there is only one client, it is moved to the AP that is closer to it. 
        if nb_clients > 1:
            overall_tenant_addr_rate, overall_tenant_addr_occupancy, handover_hwaddr, old_overall_tenant_addr_rate, old_overall_tenant_addr_occupancy = self.best_handover_search(station, stats, disable_old_wtp)
        else:
            overall_tenant_addr_rate, overall_tenant_addr_occupancy, handover_hwaddr, old_overall_tenant_addr_rate, old_overall_tenant_addr_occupancy = self.rssi_handover_search(station, stats, client_ix, disable_old_wtp)

        if handover_hwaddr == attached_hwaddr:
            self.log.info("NO HANDOVER NEEDED")
            return

        self.log.info("BETTER HANDOVER FOUND")
        self.log.info("The overall rate of this tenant-address BEFORE the handover is %d (Mbps)", old_overall_tenant_addr_rate)
        self.log.info("The overall occupancy of this tenant-address BEFORE the handover is %d (ms)", old_overall_tenant_addr_occupancy)
        self.log.info("The overall rate of this tenant-address AFTER the handover would be %d (Mbps)", overall_tenant_addr_rate)
        self.log.info("The overall occupancy of this tenant-address AFTER the handover would be %d (ms)", overall_tenant_addr_occupancy)
        self.log.info("The handover must be performed from the AP %s to the AP %s", attached_hwaddr, handover_hwaddr)

        # A copy of the client data is stored and it is restored after the handover
        for index, entry in enumerate(self.mcast_clients):
            if entry.addr == station:
                entry.rssi = stats[handover_hwaddr]['rssi']
                entry.attached_hwaddr = handover_hwaddr
                self.handover_clients[entry.addr] = entry
                break

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

        # Updates the client information in the corresponding APs
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == handover_hwaddr:
                entry.attached_clients = entry.attached_clients + 1
                entry.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
            elif entry.block.hwaddr == attached_hwaddr:
                entry.attached_clients = entry.attached_clients - 1
                entry.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB

        # The rates must be recomputed after the handover
        self.legacy_mcast_compute()


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
        lvap_info.addr = lvap.addr
        lvap_info.attached_hwaddr = default_block.hwaddr

        # If this lvap is created due to a handover, its information must be restored
        if lvap.addr in self.handover_clients:
            lvap_info.rssi = self.handover_clients[lvap_info.addr].rssi
            lvap_info.rx_pkts = self.handover_clients[lvap_info.addr].rx_pkts
            lvap_info.rates = self.handover_clients[lvap_info.addr].rates
            lvap_info.wtps = self.handover_clients[lvap_info.addr].wtps
            lvap_info.higher_thershold_ewma_rates = self.handover_clients[lvap_info.addr].higher_thershold_ewma_rates
            lvap_info.higher_thershold_cur_prob_rates = self.handover_clients[lvap_info.addr].higher_thershold_cur_prob_rates
            lvap_info.highest_rate = self.handover_clients[lvap_info.addr].highest_rate
            lvap_info.highest_cur_prob_rate = self.handover_clients[lvap_info.addr].highest_cur_prob_rate
            del self.handover_clients[lvap_info.addr]

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
                if entry.last_prob_update == 0:
                    entry.last_prob_update = time.time()

                tx_policy = entry.block.tx_policies[self.mcast_addr] 

                # If there is no clients, the default mode is DMS
                if entry.attached_clients == 0:
                    entry.mode = TX_MCAST_DMS_H
                    tx_policy.mcast = TX_MCAST_DMS
                # If there is only one client attached to this AP, the information is sent in DMS mode
                # The rate is also calculated.
                elif entry.attached_clients == 1:
                    self.calculate_wtp_rate(entry)
                    entry.mode = TX_MCAST_DMS_H
                    tx_policy.mcast = TX_MCAST_DMS
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
                        rate = self.calculate_wtp_rate(entry)
                        tx_policy.mcast = TX_MCAST_LEGACY
                        if entry.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
                            tx_policy.mcs = [int(rate)]
                        elif entry.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
                            tx_policy.mcs = [int(rate)]
                        entry.last_prob_update = time.time()
                        entry.mode = TX_MCAST_LEGACY_H


    def calculate_wtp_rate(self, mcast_wtp):
        if mcast_wtp.last_rssi_change > 0 and (time.time() - mcast_wtp.last_rssi_change > self.rssi_stabilizing_period):
            mcast_wtp.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB
        elif mcast_wtp.last_rssi_change > 0 and (time.time() - mcast_wtp.last_rssi_change < self.rssi_stabilizing_period):
            mcast_wtp.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB

        calculated_rate, highest_cur_prob_rate, thershold_intersection_list, thershold_highest_cur_prob_rate_intersection_list = self.multicast_rate(mcast_wtp.block.hwaddr, None, None)
        
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

        mcast_wtp.rate[self.mcast_addr] = best_rate
        mcast_wtp.cur_prob_rate[self.mcast_addr] = best_highest_cur_prob_rate

        # The rate is selected according to the probability used in that moment. 
        if mcast_wtp.prob_measurement[self.mcast_addr] == MCAST_EWMA_PROB:
            return best_rate
        elif mcast_wtp.prob_measurement[self.mcast_addr] == MCAST_CUR_PROB:
            return best_highest_cur_prob_rate


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
            if old_client is not None and entry.addr == old_client:
                continue

            if (entry.attached_hwaddr == hwaddr) or (new_client is not None or entry.addr == new_client):
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
            if entry.attached_clients == 0:
                continue

            # It obtains the most appropiate rate
            if entry.last_rssi_change is not None and (time.time() - entry.last_rssi_change > self.rssi_stabilizing_period):
                entry.prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB
            elif entry.last_rssi_change > 0 and (time.time() - entry.last_rssi_change < self.rssi_stabilizing_period):
                entry.prob_measurement[self.mcast_addr] = MCAST_CUR_PROB

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

            tx_policy = entry.block.tx_policies[self.mcast_addr]
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

        if minimum_required_pkts > highest_value:
            self.mcast_wtps[wtp_index].prob_measurement[self.mcast_addr] = MCAST_CUR_PROB
        else:
            self.mcast_wtps[wtp_index].prob_measurement[self.mcast_addr] = MCAST_EWMA_PROB


    # Calculates the global occupancy rate for the current situation (without performing any handover)
    def overall_occupancy_rate_calculation(self, aps_info, dst_addr):
        overall_tenant_rate = 0
        overall_tenant_occupancy = 0

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr not in aps_info:
                continue

            if entry.attached_clients > 0:
                if entry.prob_measurement[dst_addr] == MCAST_EWMA_PROB:
                    overall_tenant_rate = overall_tenant_rate + entry.rate[dst_addr]
                    overall_tenant_occupancy = overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[dst_addr], entry.last_tx_bytes[dst_addr], entry.rate[dst_addr])
                elif entry.prob_measurement[dst_addr] == MCAST_CUR_PROB:
                    overall_tenant_rate = overall_tenant_rate + entry.cur_prob_rate[dst_addr]
                    overall_tenant_occupancy = overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[dst_addr], entry.last_tx_bytes[dst_addr], entry.cur_prob_rate[dst_addr])
        return overall_tenant_rate, overall_tenant_occupancy


    def handover_overall_rate_calculation(self, aps_info, dst_addr, evaluated_hwaddr, new_wtp_highest_cur_prob_rate, wtp_addr, old_wtp_new_rate, disable_old_wtp):
        future_overall_tenant_rate = 0

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr not in aps_info:
                continue
            if entry.block.hwaddr == evaluated_hwaddr:
                future_overall_tenant_rate = future_overall_tenant_rate + new_wtp_highest_cur_prob_rate
            elif entry.block.hwaddr == wtp_addr and disable_old_wtp is False:
                future_overal_tenant_rate = future_overall_tenant_rate + old_wtp_new_rate
            elif entry.block.hwaddr != wtp_addr and entry.block.hwaddr != evaluated_hwaddr:
                if entry.attached_clients > 0:
                    if entry.prob_measurement[dst_addr] == MCAST_EWMA_PROB:
                        future_overall_tenant_rate = future_overall_tenant_rate + entry.rate[dst_addr]
                    elif entry.prob_measurement[dst_addr] == MCAST_CUR_PROB:
                        future_overall_tenant_rate = future_overall_tenant_rate + entry.cur_prob_rate[dst_addr]

        return future_overall_tenant_rate


    def handover_overall_channel_occupancy_calculation(self, aps_info, dst_addr, evaluated_hwaddr, new_wtp_highest_cur_prob_rate, wtp_addr, old_wtp_new_rate, disable_old_wtp):
        future_overall_tenant_occupancy = 0

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr not in aps_info:
                continue
            if entry.block.hwaddr == evaluated_hwaddr:
                future_overall_tenant_occupancy = future_overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[dst_addr], entry.last_tx_bytes[dst_addr], new_wtp_highest_cur_prob_rate)
            elif entry.block.hwaddr == wtp_addr and disable_old_wtp is False:
                future_overall_tenant_occupancy = future_overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[dst_addr], entry.last_tx_bytes[dst_addr], old_wtp_new_rate)
            elif entry.block.hwaddr != wtp_addr and entry.block.hwaddr != evaluated_hwaddr:
                if entry.attached_clients > 0:
                    if entry.prob_measurement[dst_addr] == MCAST_EWMA_PROB:
                        future_overall_tenant_occupancy = future_overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[dst_addr], entry.last_tx_bytes[dst_addr], entry.rate[dst_addr])
                    elif entry.prob_measurement[dst_addr] == MCAST_CUR_PROB:
                        future_overall_tenant_occupancy = future_overall_tenant_occupancy + self.packet_transmission_time(entry.last_tx_pkts[dst_addr], entry.last_tx_bytes[dst_addr], entry.cur_prob_rate[dst_addr])                        

        return future_overall_tenant_occupancy


    def packet_transmission_time(self, last_tx_pkts, last_tx_bytes, rate):
        avg_pkt_size = 0

        if last_tx_pkts > 0:
            avg_pkt_size = float(last_tx_bytes / last_tx_pkts)
        else:
            avg_pkt_size = self.current_transmission_avg_pkt_size()

        return float((avg_pkt_size * 8) / rate)
        

    def current_transmission_avg_pkt_size(self):
        avg_pkt_size = 0
        pkts_counter = 0
        bytes_counter = 0

        for index, entry in enumerate(self.mcast_wtps):
            if entry.attached_clients > 0 and entry.last_tx_pkts[self.mcast_addr] > 0 and entry.last_tx_bytes[self.mcast_addr] > 0:
                pkts_counter = pkts_counter + entry.last_tx_pkts[self.mcast_addr]
                bytes_counter = bytes_counter + entry.last_tx_bytes[self.mcast_addr]

        if pkts_counter > 0 and bytes_counter > 0:
            avg_pkt_size = bytes_counter / pkts_counter
            return avg_pkt_size
        
        return 1500


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


    def best_handover_search(self, station, stats, disable_old_wtp):
        evaluated_lvap = RUNTIME.lvaps[station]
        wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_wtp_rate_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_rssi = 0
        best_rate = 6
        new_wtps_possible_rates = dict()
        new_wtps_old_rates = dict()
        new_overall_tenant_addr_rate = dict()
        new_overall_tenant_addr_occupancy = dict()
        old_wtp_old_rate = None

        # The CURRENT PROB should be taken into account. It's a quick change
        # "old" wtp rate. 
        old_wtp_new_rate, old_wtp_new_highest_cur_prob_rate = self.handover_rate_compute(wtp_addr, station, None)
        if old_wtp_new_rate is None or old_wtp_new_highest_cur_prob_rate is None:
            return

        # "new" wtp rate
        # check the possible rate in all the wtps
        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr in stats and entry.block.hwaddr != wtp_addr:
                new_wtp_best_rate, new_wtp_highest_cur_prob_rate = self.handover_rate_compute(entry.block.hwaddr, None, station)
                new_wtps_possible_rates[entry.block.hwaddr] = new_wtp_highest_cur_prob_rate
                new_overall_tenant_addr_rate[entry.block.hwaddr] = self.handover_overall_rate_calculation(stats, self.mcast_addr, entry.block.hwaddr, new_wtp_highest_cur_prob_rate, wtp_addr, old_wtp_new_rate, disable_old_wtp)
                new_overall_tenant_addr_occupancy[entry.block.hwaddr] = self.handover_overall_channel_occupancy_calculation(stats, self.mcast_addr, entry.block.hwaddr, new_wtp_highest_cur_prob_rate, wtp_addr, old_wtp_new_rate, disable_old_wtp)
                if entry.prob_measurement == MCAST_EWMA_PROB:
                    new_wtps_old_rates[entry.block.hwaddr] = entry.rate[self.mcast_addr]
                elif entry.prob_measurement == MCAST_CUR_PROB:
                    new_wtps_old_rates[entry.block.hwaddr] = entry.cur_prob_rate[self.mcast_addr]
            elif entry.block.addr == wtp_addr:
                if entry.prob_measurement == MCAST_EWMA_PROB:
                    old_wtp_old_rate = entry.rate[self.mcast_addr]
                elif entry.prob_measurement == MCAST_CUR_PROB:
                    old_wtp_old_rate = entry.rate[self.mcast_addr]

        old_overall_tenant_addr_rate, old_overall_tenant_addr_occupancy  = self.overall_occupancy_rate_calculation(stats, self.mcast_addr)

        # Tradeoff between the rates. 
        best_overall_tenant_addr_rate = old_overall_tenant_addr_rate
        best_overall_tenant_addr_occupancy = old_overall_tenant_addr_occupancy
        best_overall_tenant_addr_hwaddr = wtp_addr

        # Channel occupancy approach
        for key, value in new_overall_tenant_addr_occupancy.items():
            # If the new global value is worse than the previous one or is below a given RSSI thershold, the handover to this AP is not worthy
            if value < best_overall_tenant_addr_occupancy \
            or (value == best_overall_tenant_addr_occupancy and stats[key]['rssi'] > stats[best_overall_tenant_addr_hwaddr]['rssi']) \
            and stats[key]['rssi'] > self.rssi_thershold:
                best_overall_tenant_addr_occupancy = value
                best_overall_tenant_addr_hwaddr = key
                best_overall_tenant_addr_rate = new_overall_tenant_addr_rate[key]

        # If the current combination is the most optimum option in terms of channel occupancy, but the link quality for this client is below the 
        # defined RSSI thershold, looking for a best AP (if possible) is necessary
        if best_overall_tenant_addr_hwaddr == wtp_addr and stats[wtp_addr]['rssi'] <= self.rssi_thershold:
            new_overall_tenant_addr_occupancy_rssi_above_thershold = dict()
            new_overall_tenant_addr_occupancy_rssi_below_thershold = dict()
            # Try to find the next best occupancy rate in which the new AP offers an RSSI value higher than the thershold
            for key, value in new_overall_tenant_addr_occupancy.items():
                if stats[key]['rssi'] > self.rssi_thershold:
                    new_overall_tenant_addr_occupancy_rssi_above_thershold[key] = value
                elif stats[key]['rssi'] < self.rssi_thershold and stats[key]['rssi'] > stats[wtp_addr]['rssi']:
                    new_overall_tenant_addr_occupancy_rssi_below_thershold[key] = value
            # It picks the WTP that offers the minimum occupancy rate among those that has an RSSI level above the defined thershold
            if new_overall_tenant_addr_occupancy_rssi_above_thershold:
                best_overall_tenant_addr_hwaddr = min(new_overall_tenant_addr_occupancy_rssi_above_thershold, key=new_overall_tenant_addr_occupancy_rssi_above_thershold.get)
                best_overall_tenant_addr_occupancy = new_overall_tenant_addr_occupancy_rssi_above_thershold[best_overall_tenant_addr_hwaddr]
                best_overall_tenant_addr_rate = new_overall_tenant_addr_rate[best_overall_tenant_addr_hwaddr]
            # In the worst case, if any AP offers an RSSI above the thershold, it picks the one that having an RSSI level higher than the current one, 
            # offers the minimum occupancy rate. 
            elif new_overall_tenant_addr_occupancy_rssi_below_thershold:
                best_overall_tenant_addr_hwaddr = min(new_overall_tenant_addr_occupancy_rssi_below_thershold, key=new_overall_tenant_addr_occupancy_rssi_below_thershold.get)
                best_overall_tenant_addr_occupancy = new_overall_tenant_addr_occupancy_rssi_below_thershold[best_overall_tenant_addr_hwaddr]
                best_overall_tenant_addr_rate = new_overall_tenant_addr_rate[best_overall_tenant_addr_hwaddr]

        return best_overall_tenant_addr_rate, best_overall_tenant_addr_occupancy, best_overall_tenant_addr_hwaddr, old_overall_tenant_addr_rate, old_overall_tenant_addr_occupancy


    def rssi_handover_search(self, station, stats, client_ix, disable_old_wtp):
        evaluated_lvap = RUNTIME.lvaps[EtherAddress(station)]
        wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_wtp_addr = next(iter(evaluated_lvap.downlink.keys())).hwaddr
        best_rssi = stats[wtp_addr]['rssi']
        old_wtp_old_rate = stats[wtp_addr]['rate']
        best_rate = stats[wtp_addr]['rate']

        old_wtp_new_rate, old_wtp_new_highest_cur_prob_rate = self.handover_rate_compute(wtp_addr, station, None)
        if old_wtp_new_rate is None or old_wtp_new_highest_cur_prob_rate is None:
            return
        old_overall_tenant_addr_rate, old_overall_tenant_addr_occupancy  = self.overall_occupancy_rate_calculation(stats, self.mcast_addr)

        # It checks if any wtp offers a better RSSI than the one is currently attached
        for key, value in stats.items():
            if value['rssi'] > best_rssi and key != best_wtp_addr and value['rssi'] > self.rssi_thershold:
                best_rssi = value['rssi']
                best_wtp_addr = key

        if best_wtp_addr == wtp_addr:
            best_rate = self.mcast_clients[client_ix].highest_rate
            best_overall_tenant_addr_occupancy = old_overall_tenant_addr_occupancy
        else:
            best_rate = self.mcast_clients[client_ix].highest_cur_prob_rate
            best_overall_tenant_addr_occupancy = self.handover_overall_channel_occupancy_calculation(stats, self.mcast_addr, best_wtp_addr, best_rate, wtp_addr, old_wtp_new_rate, disable_old_wtp)

        return best_rate, best_overall_tenant_addr_occupancy, best_wtp_addr, old_overall_tenant_addr_rate, old_overall_tenant_addr_occupancy


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
        out['mcast_addr'] = self.mcast_addr
        out['rssi_thershold'] = self.rssi_thershold

        return out
                                    


def launch(tenant_id, every=500, rssi={}, rx_pkts={}, aps={}, mcast_clients=[], mcast_wtps=[]):
    """ Initialize the module. """

    return MCastMobilityManager(tenant_id=tenant_id, every=every, rssi=rssi, rx_pkts=rx_pkts, aps=aps, mcast_clients=mcast_clients, mcast_wtps=mcast_wtps)
