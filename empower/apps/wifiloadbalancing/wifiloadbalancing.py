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

        # register lvap join/leave events
        self.lvapjoin(callback=self.lvap_join_callback)
        self.wtpup(callback=self.wtp_up_callback)

    def lvap_join_callback(self, lvap):
        """Called when a new LVAP joins the network."""

        self.bin_counter(lvap=lvap.addr,
                         every=self.every,
                         callback=self.counters_callback)

        self.ucqm_data[lvap.blocks[0].addr.to_str() + lvap.addr.to_str()] = \
            {
                'rssi': None,
                'wtp': lvap.blocks[0],
                'lvap': lvap,
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

            self.ucqm(block=block,
                      every=self.every,
                      callback=self.ucqm_callback)

            self.wifistats(block=block,
                           every=self.every,
                           callback=self.wifi_stats_callback)

            self.conflict_aps[block.addr] = []
            self.aps_clients_matrix[block.addr] = []
            self.aps_channel_utilization[block.addr] = 0
            self.scheduling_attempts[block.addr] = 0
            self.aps_counters[block.addr] = {}

    def counters_callback(self, stats):
        """ New stats available. """

        lvap = RUNTIME.lvaps[stats.lvap]

        if not stats.tx_bytes_per_second or not stats.rx_bytes_per_second:
            return

        cnt = self.aps_counters[lvap.blocks[0].addr][lvap.addr]

        cnt['tx_bytes_per_second'] = stats.tx_bytes_per_second[0]
        cnt['rx_bytes_per_second'] = stats.rx_bytes_per_second[0]

    def wifi_stats_callback(self, stats):
        """ New stats available. """

        # If there are no clients attached, it is not necessary to check the
        # channel utilization
        if not self.aps_clients_matrix[stats.block.addr]:
            self.aps_channel_utilization[stats.block.addr] = 0
            return

        bytes_per_second = reduce(lambda x, y: dict((k, v + y[k]) for k, v in x.items()), self.aps_counters[stats.block.addr].values())
        if (stats.tx_per_second + stats.rx_per_second) == 0:
            if (bytes_per_second['tx_bytes_per_second'] + bytes_per_second['rx_bytes_per_second']) == 0:
                self.aps_channel_utilization[stats.block.addr] = 0
            return

        previous_utilization = self.aps_channel_utilization[stats.block.addr]
        self.aps_channel_utilization[stats.block.addr] = (stats.tx_per_second + stats.rx_per_second)
        average_utilization = self.estimate_global_channel_utilization()
        channel_utilization_difference = self.evalute_channel_utilization_difference(previous_utilization, self.aps_channel_utilization[stats.block.addr], average_utilization)

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
                        'active':active_flag
                    }
                else:
                    self.ucqm_data[key]['rssi'] = lvap['mov_rssi']
                    self.ucqm_data[key]['active'] = active_flag
                # Conversion of the data structure to obtain the conflict APs
                if poller.block not in self.clients_aps_matrix[lvap['addr']]:
                    self.clients_aps_matrix[lvap['addr']].append(poller.block)
            elif key in self.ucqm_data:
                del self.ucqm_data[key]

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

    def loop(self):
        """ Periodic job. """

        if self.handover_data:
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
            {str(k): {'wtp':v['wtp'].addr, 'lvap':v['lvap'].addr, 'rssi':v['rssi'], \
                     'active':v['active']} for k, v in self.ucqm_data.items()}
        return out


def launch(tenant_id, every=1000):
    """ Initialize the module. """

    return WifiLoadBalancing(tenant_id=tenant_id, every=every)
