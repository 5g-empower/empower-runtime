#!/usr/bin/env python3
#
# Copyright (c) 2017, Estefanía Coronado
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

"""Simple wifi load balancing management app."""

from empower.core.app import EmpowerApp
from empower.core.resourcepool import BT_HT20
from empower.datatypes.etheraddress import EtherAddress
from empower.main import RUNTIME
from empower.maps.ucqm import UCQMWorker
from empower.wifi_stats.wifi_stats import WiFiStatsWorker

from functools import reduce
from collections import Counter
import time
import sys

RSSI_LIMIT = 10

class WifiLoadBalancing(EmpowerApp):
    """WifiLoadBalancing app.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.wifiloadbalancing.wifiloadbalancing \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada00

    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # app parameters
        self.ucqm_data = {}
        self.conflict_aps = {}
        self.aps_clients_matrix = {}
        self.clients_aps_matrix = {}

        self.handover_data = {}
        self.unsuccessful_handovers = {}
        self.aps_channel_utilization = {}
        self.scheduling_attempts = {}
        self.aps_counters = {}
        self.last_handover_time = 0
        self.coloring_channels  = {36, 40, 1}
        self.initial_setup = True

        # register lvap join/leave events
        self.lvapjoin(callback=self.lvap_join_callback)
        self.wtpup(callback=self.wtp_up_callback)

    def lvap_join_callback(self, lvap):
        """Called when a new LVAP joins the network."""

        self.ucqm_data[lvap.blocks[0].addr.to_str() + lvap.addr.to_str()] = \
            {
                'rssi': None,
                'wtp': lvap.blocks[0],
                'lvap': lvap,
                'channel': lvap.blocks[0].channel,
                'active': 1
            }

        self.aps_clients_matrix[lvap.blocks[0].addr].append(lvap)
        self.clients_aps_matrix[lvap.addr] = []
        self.clients_aps_matrix[lvap.addr].append(lvap.blocks[0])
        self.aps_counters[lvap.blocks[0].addr][lvap.addr] = \
            {
                'tx_bytes_per_second': 0,
                'rx_bytes_per_second': 0
            }

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        for block in wtp.supports:
            self.ucqm(block=block, every=self.every, callback=self.ucqm_callback)
            self.wifistats(block=block, every=self.every, callback=self.wifi_stats_callback)

            self.conflict_aps[block.addr] = []
            self.aps_clients_matrix[block.addr] = []
            self.aps_channel_utilization[block.addr] = 0
            self.scheduling_attempts[block.addr] = 0
            self.aps_counters[block.addr] = {}

    def wifi_stats_callback(self, stats):
        """ New stats available. """

        self.log.info("Statistical information received from %s. Tx occupancy: %f Rx: occupancy %f" 
                    %(stats.block.addr.to_str(), stats.tx_per_second, stats.rx_per_second))

        # If there are no clients attached, it is not necessary to check the channel utilization
        if not self.aps_clients_matrix[stats.block.addr]:
            self.aps_channel_utilization[stats.block.addr] = 0
            return

        if (stats.tx_per_second + stats.rx_per_second) == 0:
            self.aps_channel_utilization[stats.block.addr] = 0
            return
        
        previous_utilization = self.aps_channel_utilization[stats.block.addr]
        self.aps_channel_utilization[stats.block.addr] = (stats.tx_per_second + stats.rx_per_second)
        average_utilization = self.estimate_global_channel_utilization()
        channel_utilization_difference = self.evalute_channel_utilization_difference(previous_utilization, self.aps_channel_utilization[stats.block.addr], average_utilization)

        if self.initial_setup:
            return
        if channel_utilization_difference is True and len(self.aps_clients_matrix[stats.block.addr]) > 1:
            self.scheduling_attempts[stats.block.addr] += 1
        if (time.time() - self.last_handover_time) < 5 or len(self.handover_data) != 0:
            return

        if self.scheduling_attempts[stats.block.addr] >= 3:
            self.scheduling_attempts[stats.block.addr] = 0
            self.log.info("Evaluate traffic balancing for block %s" % stats.block.addr)
            self.evaluate_lvap_scheduling(stats.block)

    def ucqm_callback (self, poller):
        """Called when a UCQM response is received from a WTP."""

        lvaps = RUNTIME.tenants[self.tenant.tenant_id].lvaps
        channel_changes = False

        for lvap in poller.maps.values():
            key = poller.block.addr.to_str() + lvap['addr'].to_str()
            if lvap['addr'] in lvaps and lvaps[lvap['addr']].wtp:
                active_flag = 1
                if (lvaps[lvap['addr']].wtp.addr != poller.block.addr):
                    active_flag = 0
                elif ((lvaps[lvap['addr']].wtp.addr == poller.block.addr and (lvaps[lvap['addr']].association_state == False))):
                    active_flag = 0
                if key not in self.ucqm_data:
                    self.ucqm_data[key] = \
                    {
                        'rssi': lvap['mov_rssi'],
                        'wtp': poller.block,
                        'lvap': lvaps[lvap['addr']],
                        'channel': poller.block.channel,
                        'active':active_flag
                    }
                    channel_changes = True
                else:
                    self.ucqm_data[key]['rssi'] = lvap['mov_rssi']
                    self.ucqm_data[key]['active'] = active_flag
                    if self.ucqm_data[key]['channel'] != poller.block.channel:
                        self.ucqm_data[key]['channel'] = poller.block.channel
                        channel_changes = True

                # Conversion of the data structure to obtain the conflict APs
                if poller.block not in self.clients_aps_matrix[lvap['addr']]:
                    self.clients_aps_matrix[lvap['addr']].append(poller.block)
            elif key in self.ucqm_data:
                del self.ucqm_data[key]

        if channel_changes:
            self.conflict_graph()

    def conflict_graph(self):

        initial_conflict_graph = self.conflict_aps

        for wtp_list in self.clients_aps_matrix.values():
            for wtp in wtp_list:
                for conflict_wtp in wtp_list:
                    if conflict_wtp != wtp and (conflict_wtp not in self.conflict_aps[wtp.addr]):
                        self.conflict_aps[wtp.addr].append(conflict_wtp)

    def evaluate_lvap_scheduling(self, block):

        ap_candidates = {}
        best_metric = sys.maxsize
        new_wtp = None
        new_lvap = None

        for sta in self.aps_clients_matrix[block.addr]:
            for wtp in self.clients_aps_matrix[sta.addr]:
                key = wtp.addr.to_str() + sta.addr.to_str()
                if wtp == block or self.aps_channel_utilization[wtp.addr] > self.aps_channel_utilization[block.addr] or \
                    self.ucqm_data[key]['rssi'] < -85:
                    continue
                if key in self.unsuccessful_handovers:
                    self.unsuccessful_handovers[key]['handover_retries'] += 1
                    if self.unsuccessful_handovers[key]['handover_retries'] < 5:
                        continue
                    del self.unsuccessful_handovers[key]

                conflict_occupancy = self.aps_channel_utilization[wtp.addr]
                for neighbour in self.conflict_aps[wtp.addr]:
                    if neighbour.channel == wtp.channel:
                        conflict_occupancy += self.aps_channel_utilization[neighbour.addr]
                wtp_info = \
                    {
                        'wtp': wtp,
                        #'metric' : abs(self.ucqm_data[key]['rssi']) * self.aps_channel_utilization[wtp.addr],
                        'metric': abs(self.ucqm_data[key]['rssi']) * conflict_occupancy,
                        'rssi': self.ucqm_data[key]['rssi']
                    }
                ap_candidates[sta.addr] = []
                ap_candidates[sta.addr].append(wtp_info)

        ### Evaluation
        for sta, wtps in ap_candidates.items():
            for ap in wtps:
                if (ap['metric'] < best_metric) or \
                    (ap['metric'] == best_metric and self.aps_channel_utilization[ap['wtp'].addr] < self.aps_channel_utilization[new_wtp.addr]):
                    best_metric = ap['metric']
                    new_wtp = ap['wtp']
                    new_lvap = RUNTIME.lvaps[sta]

        if new_wtp is None or new_lvap is None:
            return

        try:
            new_lvap.blocks = new_wtp
            self.last_handover_time = time.time()
            self.handover_data[new_lvap.addr] = \
                {
                    'old_ap': block,
                    'handover_ap': new_wtp,
                    'previous_channel_utilization': self.estimate_global_channel_utilization(),
                    'handover_time': time.time()
                }
            self.transfer_block_data(block, new_wtp, new_lvap)
        except ValueError:
            self.log.info("Handover already in progress for lvap %s" % lvap.addr.to_str())
            return

    def transfer_block_data(self, src_block, dst_block, lvap):

        self.scheduling_attempts[lvap.blocks[0].addr] = 0
        self.aps_clients_matrix[src_block.addr].remove(lvap)
        self.aps_clients_matrix[dst_block.addr].append(lvap)

        del self.aps_counters[src_block.addr][lvap.addr]
        self.aps_counters[dst_block.addr][lvap.addr] = \
            {
                'tx_bytes_per_second': 0,
                'rx_bytes_per_second': 0
            }

    def estimate_global_channel_utilization(self):

        utilization = 0
        for value in self.aps_channel_utilization.values():
            utilization += value
        
        return (utilization/len(self.aps_channel_utilization))

    def check_handover_performance(self):

        checked_clients = []
        for lvap, value in self.handover_data.items():
            if (time.time() - value['handover_time']) < 5:
                continue
            current_channel_utilization = self.estimate_global_channel_utilization()
            if value['previous_channel_utilization'] < current_channel_utilization and (current_channel_utilization - value['previous_channel_utilization']) > 20:
                self.revert_handover(lvap, current_channel_utilization)
            checked_clients.append(lvap)

        for entry in checked_clients:
            del self.handover_data[entry]

    def revert_handover(self, lvap_addr, current_channel_utilization):

        handover_ap = self.handover_data[lvap_addr]['handover_ap']
        old_ap = self.handover_data[lvap_addr]['old_ap']
        lvap = RUNTIME.lvaps[lvap_addr]

        try:
            lvap.blocks = old_ap
            self.last_handover_time = time.time()
            key = handover_ap.addr.to_str() + lvap.addr.to_str()
            self.unsuccessful_handovers[key] = \
                {
                    'rssi': self.ucqm_data[key]['rssi'],
                    'previous_channel_utilization': current_channel_utilization,
                    'handover_retries': 0,
                    'old_ap': old_ap,
                    'handover_ap': handover_ap
                }
            self.transfer_block_data(handover_ap, old_ap, lvap)
        except ValueError:
            self.log.info("Handover already in progress for lvap %s" % lvap.addr.to_str())
            return

    def evalute_channel_utilization_difference(self, old_occupancy, new_occupancy, average_occupancy):

        if new_occupancy <= 10:
            return False
        if new_occupancy < (average_occupancy * 0.8) or new_occupancy > (average_occupancy * 1.2) or \
            new_occupancy < (old_occupancy * 0.8) or new_occupancy > (old_occupancy * 1.2):
            return True

        return False

    def find_best_candidate(self, network_graph, attempts):
        candidates_with_add_info = [
        (
            -len({attempts[neighbour] for neighbour in network_graph[n] if neighbour in attempts}), # channels that should not be assigned
            -len({neighbour for neighbour in network_graph[n] if neighbour not in attempts}), # aps not assigned yet
            n
        ) for n in network_graph if n not in attempts]

        candidates_with_add_info.sort()
        candidates = [n for _,_,n in candidates_with_add_info]

        if candidates:
            candidate = candidates[0]
            return candidate

        return None

    def solve_channel_assignment(self, network_graph, channels, attempts):
        ap_addr = self.find_best_candidate(network_graph, attempts)
        if ap_addr is None:
            return attempts # Solution is found

        for c in channels - {attempts[neighbour] for neighbour in network_graph[ap_addr] if neighbour in attempts}:
            attempts[ap_addr] = c
            if self.solve_channel_assignment(network_graph, channels, attempts):
                return attempts
            else:
                del attempts[ap_addr]

        return None

    def network_coloring(self):

        if self.clients_aps_matrix:
            return

        network_graph = {}

        for block, conflict_list in self.conflict_aps.items():
            network_graph[block.to_str()] = set([neighbour.addr.to_str() for neighbour in conflict_list if conflict_list])
        network_graph = {block:neighbour_set for block,neighbour_set in network_graph.items() if neighbour_set}
        channel_assignment = self.solve_channel_assignment(network_graph, self.coloring_channels, dict())

        if not channel_assignment:
            return

        for block_addr, channel in channel_assignment.items():
            self.switch_channel(block_addr, channel)

    def switch_channel(self, req_block_addr, channel):

        self.log.info("Performing channel switch for block %s to channel %d" %(req_block_addr, channel))

        wtps = RUNTIME.tenants[self.tenant.tenant_id].wtps

        for wtp in wtps.values():
            for block in wtp.supports:
                if block.addr.to_str() == req_block_addr and block.channel == channel:
                    return
                elif block.addr.to_str() != req_block_addr:
                    continue

                self.delete_block_worker(block)
                block.radio.connection.send_wtp_channel_update_request(block, channel)
                block.channel = channel

                for lvap in self.aps_clients_matrix[block.addr]:
                    self.ucqm_data[block.addr.to_str() + lvap.addr.to_str()]['channel'] = channel

                self.ucqm(block=block, every=self.every, callback=self.ucqm_callback)
                self.wifistats(block=block, every=self.every, callback=self.wifi_stats_callback)

    def delete_block_worker(self, block):

        ucqm_worker = RUNTIME.components[UCQMWorker.__module__]
        wifi_stats_worker = RUNTIME.components[WiFiStatsWorker.__module__]

        for module_id in list(ucqm_worker.modules.keys()):
            ucqm_mod = ucqm_worker.modules[module_id]
            if block == ucqm_mod.block:
                ucqm_worker.remove_module(module_id)

        for module_id in list(wifi_stats_worker.modules.keys()):
            wifi_stats_mod = wifi_stats_worker.modules[module_id]
            if block == wifi_stats_mod.block:
                wifi_stats_worker.remove_module(module_id)
                return

    def loop(self):
        """ Periodic job. """

        if self.initial_setup:
            self.network_coloring()
            self.initial_setup = False
        elif self.handover_data:
            self.check_handover_performance()

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['conflict_aps'] = \
            {str(k): (''.join(block.addr.to_str()) for block in v) for k, v in self.conflict_aps.items()}
        out['aps_clients_matrix'] = \
            {str(k): (''.join(lvap.addr.to_str()) for lvap in v) for k, v in self.aps_clients_matrix.items()}
        out['clients_aps_matrix'] = \
            {str(k): (''.join(block.addr.to_str()) for block in v) for k, v in self.clients_aps_matrix.items()}
        out['handover_data'] = \
            {str(k): {'old_ap':v['old_ap'].addr, 'handover_ap':v['handover_ap'].addr,  \
                        'previous_channel_utilization':v['previous_channel_utilization'], \
                        'handover_time':v['handover_time']} for k, v in self.handover_data.items()}
        out['unsuccessful_handovers'] = \
            {str(k): {'old_ap':v['old_ap'].addr, 'handover_ap':v['handover_ap'].addr, 'rssi':v['rssi'], \
                        'previous_channel_utilization':v['previous_channel_utilization'], 'handover_retries':v['handover_retries']} \
                        for k, v in self.unsuccessful_handovers.items()}
        out['aps_channel_utilization'] = \
            {str(k): v for k, v in self.aps_channel_utilization.items()}
        out['scheduling_attempts'] = \
            {str(k): v for k, v in self.scheduling_attempts.items()}
        out['ucqm_data'] = \
            {str(k): {'wtp':v['wtp'].addr, 'lvap':v['lvap'].addr, 'rssi':v['rssi'], 'channel':v['channel'], \
                     'active':v['active']} for k, v in self.ucqm_data.items()}
        return out

def launch(tenant_id, every=1000):
    """ Initialize the module. """

    return WifiLoadBalancing(tenant_id=tenant_id, every=every)