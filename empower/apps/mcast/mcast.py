#!/usr/bin/env python3
#
# Copyright (c) 2019 Estefania Coronado
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

"""SDN@Play Multicast Manager."""

import sys
import json

from empower.core.app import EApp
from empower.core.app import EVERY
from empower.core.etheraddress import EtherAddress
from empower.core.txpolicy import TxPolicy
from empower.core.txpolicy import TX_MCAST
from empower.core.txpolicy import TX_MCAST_DMS
from empower.core.txpolicy import TX_MCAST_LEGACY
from empower.core.resourcepool import BT_HT20

TX_MCAST_SDNPLAY = 0x3
TX_MCAST_SDNPLAY_H = "sdn@play"


class Mcast(EApp):
    """SDN@Play Multicast Manager.

    This app implements the SDN@Play [1] algorithm.

    [1] Estefania Coronado, Elisenda Temprado Garriga, Jose Villalon, Antonio
    Garrido, Leonardo Goratti, Roberto Riggio, "SDN@Play: Software-Defined
    Multicasting in Enterprise WLANs", in IEEE Communications Magazine,
    vol. 57, no. 7, pp. 85-91, July 2019.

    Parameters:
        service_id: the application id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)
        every: the loop period in ms (optional, default 2000ms)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.mcast.mcast",
            "params": {
                "every": 2000
            }
        }
    """

    def __init__(self, service_id, project_id, every=EVERY):

        super().__init__(service_id=service_id, project_id=project_id,
                         every=every)

        self.receptors = {}
        self.receptors_mcses = {}
        self.receptors_quality = {}
        self.prob_threshold = 90.0
        self.current = 0
        self.dms = 1
        self.legacy = 9
        self.schedule = \
            [TX_MCAST_DMS] * self.dms + \
            [TX_MCAST_LEGACY] * self.legacy  # --> [DMS, LEGACY, LEGACY...]
        self._demo_mode = TX_MCAST_SDNPLAY_H
        self._services_registered = 0
        self.status = {}

    def reset_mcast_services(self, value=None):
        """Import mcast services from db."""

        self.storage['mcast_services'] = {}

        if not value:
            return

        for service in value.values():
            self.mcast_services = service

    @property
    def mcast_services(self):
        """Get the list of active mcast services."""

        return self.storage['mcast_services']

    @mcast_services.setter
    def mcast_services(self, service):
        """Add a new service.

        Expects a dict with the following format:

        {
            "ip": "224.0.1.200",
            "receivers": ["ff:ff:ff:ff:ff:ff"],
            "status": True,
            "type": "emergency"
        }
        """

        if not service:
            return

        addr = self.mcast_ip_to_ether(service["ip"])

        if addr not in self.mcast_services:

            schedule = self.schedule[-self._services_registered:] + \
                    self.schedule[:-self._services_registered]

            self.mcast_services[addr] = {
                "addr": addr,
                "ip": service["ip"],
                "mcs": 6,
                "schedule": schedule,
                "receivers": [EtherAddress(x) for x in service["receivers"]],
                "status": service["status"],
                "type": service["type"]
            }

            self._services_registered += 1

        else:

            self.mcast_services[addr]["receivers"] = \
                [EtherAddress(x) for x in service["receivers"]]
            self.mcast_services[addr]["status"] = service["status"]
            self.mcast_services[addr]["type"] = service["type"]

        self.save_service_state()

    @property
    def demo_mode(self):
        """Get demo mode."""

        return self._demo_mode

    @demo_mode.setter
    def demo_mode(self, mode):
        """Set the demo mode."""

        self._demo_mode = mode

        for addr, entry in self.mcast_services.items():

            phase = self.get_next_group_phase(addr)

            self.log.info("Mcast phase %s for group %s", TX_MCAST[phase], addr)

            for block in self.blocks():

                # fetch txp
                txp = block.tx_policies[addr]

                if mode == TX_MCAST[TX_MCAST_DMS]:

                    txp.mcast = TX_MCAST_DMS

                elif mode == TX_MCAST[TX_MCAST_LEGACY]:

                    txp.mcast = TX_MCAST_LEGACY

                    if block.band == BT_HT20:
                        txp.ht_mcs = [min(block.ht_supports)]
                    else:
                        txp.mcs = [min(block.supports)]

            if mode != TX_MCAST_SDNPLAY_H:
                entry['mcs'] = "None"

    def lvap_join(self, lvap):
        """Called when an LVAP joins a tenant."""

        service = "empower.primitives.wifircstats.wifircstats"
        self.receptors[lvap.addr] = \
            self.get_service(service, sta=lvap.addr)

    def lvap_leave(self, lvap):
        """Called when an LVAP leaves the network."""

        if lvap.addr in self.receptors:
            del self.receptors[lvap.addr]

        if lvap.addr in self.receptors_mcses:
            del self.receptors_mcses[lvap.addr]

        if lvap.addr in self.receptors_quality:
            del self.receptors_quality[lvap.addr]

    def compute_receptors_mcs(self):
        """New stats available."""

        for rcstats in self.receptors.values():

            highest_prob = 0

            sta = rcstats.sta
            keys = [float(i) for i in rcstats.rates.keys()]
            best_mcs = min(list(map(int, keys)))

            self.receptors_mcses[sta] = []

            for mcs, stats in rcstats.rates.items():
                if stats["prob"] >= self.prob_threshold:
                    self.receptors_mcses[sta].append(int(float(mcs)))
                elif stats["prob"] > highest_prob:
                    best_mcs = int(float(mcs))
                    highest_prob = stats["prob"]

            if not self.receptors_mcses[sta]:
                self.receptors_quality[sta] = False
                self.receptors_mcses[sta].append(best_mcs)
            else:
                self.receptors_quality[sta] = True

    def calculate_group_mcs(self, group_receivers):
        """Compute group MCS magic."""

        self.compute_receptors_mcs()

        if not self.receptors_mcses:
            return 0

        if False not in self.receptors_quality.values():
            mcses = []
            for lvap, rates in self.receptors_mcses.items():
                if lvap in group_receivers:
                    mcses.append(rates)

            if mcses:
                mcs_intersection = list(set.intersection(*map(set, mcses)))
                if mcs_intersection:
                    mcs = max(mcs_intersection)
                    return mcs

        mcs = sys.maxsize

        for lvap, rates in self.receptors_mcses.items():
            if lvap in group_receivers:
                mcs = min(max(rates), mcs)

        if mcs == sys.maxsize:
            mcs = 0

        return mcs

    def get_next_group_phase(self, mcast_addr):
        """Get next mcast phase to be scheduled."""

        schedule = self.mcast_services[mcast_addr]["schedule"]
        phase = schedule[self.current % len(self.schedule)]
        self.current += 1

        return phase

    @classmethod
    def mcast_ip_to_ether(cls, ip_mcast_addr):
        """Transform an IP multicast address into an Ethernet one."""

        if ip_mcast_addr is None:
            return '\x00' * 6

        # The first 24 bits are fixed according to class D IP
        # and IP multicast address convenctions
        mcast_base = '01:00:5e'

        # The 23 low order bits are mapped.
        ip_addr_bytes = str(ip_mcast_addr).split('.')

        # The first IP byte is not use,
        # and only the last 7 bits of the second byte are used.
        second_byte = int(ip_addr_bytes[1]) & 127
        third_byte = int(ip_addr_bytes[2])
        fourth_byte = int(ip_addr_bytes[3])

        mcast_upper = format(second_byte, '02x') + ':' + \
            format(third_byte, '02x') + ':' + \
            format(fourth_byte, '02x')

        return EtherAddress(mcast_base + ':' + mcast_upper)

    def loop(self):
        """ Periodic job. """

        # if the demo is now in DMS it should not calculate anything
        if self.demo_mode == TX_MCAST[TX_MCAST_DMS] or \
           self.demo_mode == TX_MCAST[TX_MCAST_LEGACY]:

            return

        for block in self.blocks():

            for addr, entry in self.mcast_services.items():

                phase = self.get_next_group_phase(addr)

                self.log.info("Mcast phase %s for group %s",
                              TX_MCAST[entry["schedule"][phase]], addr)

                # fetch txp
                if addr not in block.tx_policies:
                    block.tx_policies[addr] = TxPolicy(addr, block)

                txp = block.tx_policies[addr]

                # If the service is disabled, DMS must be the multicast mode
                if entry["status"] is False:
                    txp.mcast = TX_MCAST_DMS
                    continue

                if phase == TX_MCAST_DMS:

                    txp.mcast = TX_MCAST_DMS

                else:

                    # compute MCS
                    temp_mcs = self.calculate_group_mcs(entry["receivers"])

                    if block.band == BT_HT20:
                        mcs = max(temp_mcs, min(block.ht_supports))
                    else:
                        mcs = max(temp_mcs, min(block.supports))

                    entry['mcs'] = mcs
                    txp.mcast = TX_MCAST_LEGACY

                    if block.band == BT_HT20:
                        txp.ht_mcs = [mcs]
                    else:
                        txp.mcs = [mcs]

                    # assign MCS
                    self.log.info("Block %s setting mcast %s to %s MCS %d",
                                  block, addr, TX_MCAST[TX_MCAST_DMS], mcs)

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['demo_mode'] = self.demo_mode
        out['status'] = self.status
        out['schedule'] = [TX_MCAST[x] for x in self.schedule]
        out['mcast_services'] = self.mcast_services

        return out


def launch(service_id, project_id, every=EVERY):
    """ Initialize the module. """

    return Mcast(service_id=service_id, project_id=project_id, every=every)
