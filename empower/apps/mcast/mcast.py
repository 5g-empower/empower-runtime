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

import empower.managers.apimanager.apimanager as apimanager

from empower.managers.ranmanager.lvapp.wifiapp import EWiFiApp
from empower.core.app import EVERY
from empower.core.etheraddress import EtherAddress
from empower.managers.ranmanager.lvapp.txpolicy import TxPolicy
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_DMS
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_LEGACY
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_DMS_H
from empower.managers.ranmanager.lvapp.txpolicy import TX_MCAST_LEGACY_H
from empower.managers.ranmanager.lvapp.resourcepool import BT_HT20

TX_MCAST_SDNPLAY = 0x3
TX_MCAST_SDNPLAY_H = "sdn@play"


# pylint: disable=W0223
class McastServicesHandler(apimanager.EmpowerAPIHandler):
    """Access applications' attributes."""

    URLS = [r"/api/v1/projects/([a-zA-Z0-9-]*)/apps/([a-zA-Z0-9-]*)/"
            "mcast_services/([a-zA-Z0-9:]*)/?",
            r"/api/v1/projects/([a-zA-Z0-9-]*)/apps/([a-zA-Z0-9-]*)/"
            "mcast_services/?"]

    @apimanager.validate(min_args=2, max_args=3)
    def get(self, *args, **kwargs):
        """Access the mcast_services .

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)
            [2]: the mcast service MAC address (optional)

        Example URLs:

            GET /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                mcast_services/01:00:5E:00:01:C8

            {
                addr: "01:00:5E:00:01:C8",
                ipaddress: "224.0.1.200",
                mcs: 0,
                schedule: [
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                receivers: [
                    "FF:FF:FF:FF:FF:FF"
                ],
                status: "true",
                service_type: "emergency"
            }
        """

        if len(args) == 2:
            return self.service.mcast_services

        return self.service.mcast_services[EtherAddress(args[2])]

    @apimanager.validate(returncode=204, min_args=2, max_args=2)
    def post(self, *args, **kwargs):
        """Add/update a new mcast service

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)

        Request:

            version: protocol version (1.0)
            params: the set of parameters to be set

        Parameters:

            ipaddress: the mcast IP address
            receivers: the list of mcast receptors
            status: the service status
            service_type: a label describing the service

        Example URLs:

            POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                7069c865-8849-4840-9d96-e028663a5dcf/mcast_service

            {
                "version": "1.0",
                "params": {
                    "ipaddress": "224.0.1.200",
                    "receivers": ["ff:ff:ff:ff:ff:ff"],
                    "status": "true",
                    "service_type": "emergency"
                }
            }
        """

        addr = self.service.upsert_mcast_service(**kwargs['params'])

        self.service.save_service_state()

        url = "/api/v1/projects/%s/apps/%s/mcast_service/%s" % \
            (self.service.context.project_id, self.service.service_id, addr)

        self.set_header("Location", url)

    @apimanager.validate(min_args=3, max_args=3)
    def delete(self, *args, **kwargs):
        """Delete the mcast_services .

        Args:

            [0]: the project id (mandatory)
            [1]: the app id (mandatory)
            [3]: the mcast service MAC address (mandatory)

        Example URLs:

            DELETE /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps/
                mcast_services/01:00:5E:00:01:C8
        """

        self.service.delete_mcast_service(EtherAddress(args[2]))
        self.service.save_service_state()


class Mcast(EWiFiApp):
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

    HANDLERS = [McastServicesHandler]

    def __init__(self, context, service_id, mcast_policy=TX_MCAST_SDNPLAY_H,
                 every=EVERY):

        super().__init__(context=context, service_id=service_id,
                         mcast_policy=mcast_policy, every=every)

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
        self._services_registered = 0
        self.configuration['mcast_services'] = {}

    def upsert_mcast_service(self, ipaddress, receivers, status, service_type):
        """Update/insert new mcast services.

        Expected input:

        {
            "ip": "224.0.1.200",
            "receivers": ["ff:ff:ff:ff:ff:ff"],
            "status": True,
            "type": "emergency"
        }
        """

        addr = self.mcast_ip_to_ether(ipaddress)

        if addr not in self.mcast_services:

            schedule = self.schedule[-self._services_registered:] + \
                    self.schedule[:-self._services_registered]

            self.mcast_services[addr] = {
                "addr": addr,
                "ipaddress": ipaddress,
                "mcs": 6,
                "schedule": schedule,
                "receivers": [EtherAddress(x) for x in receivers],
                "status": status,
                "service_type": service_type
            }

            self._services_registered += 1

        else:

            self.mcast_services[addr]["receivers"] = \
                [EtherAddress(x) for x in receivers]
            self.mcast_services[addr]["status"] = status
            self.mcast_services[addr]["service_type"] = service_type

        return addr

    def delete_mcast_service(self, addr):
        """Delete an mcast service."""

        if addr in self.mcast_services:
            del self.mcast_services[addr]

    @property
    def mcast_services(self):
        """Get the list of active mcast services."""

        return self.configuration['mcast_services']

    @mcast_services.setter
    def mcast_services(self, services):
        """Set the list of mcast services.

        Notice that this setter expects to receive the full list of services
        which is then parsed and saved locally.

        The following format is expected

        {
            "ff:ff:ff:ff:ff:ff": {
                "ip": "224.0.1.200",
                "receivers": ["ff:ff:ff:ff:ff:ff"],
                "status": True,
                "type": "emergency"
            }
        }
        """

        self.configuration['mcast_services'] = {}

        for service in services.values():
            self.upsert_mcast_service(service['ipaddress'],
                                      service['receivers'],
                                      service['status'],
                                      service['service_type'])

    @property
    def mcast_policy(self):
        """Get mcast policy."""

        return self.params['mcast_policy']

    @mcast_policy.setter
    def mcast_policy(self, mode):
        """Set the mcast policy."""

        if mode not in (TX_MCAST_LEGACY_H, TX_MCAST_DMS_H, TX_MCAST_SDNPLAY_H):
            raise ValueError("Invalid mcast policy %s" % mode)

        self.params['mcast_policy'] = mode

    def handle_lvap_join(self, lvap):
        """Called when an LVAP joins a tenant."""

        service = "empower.apps.wifircstats.wifircstats"
        self.receptors[lvap.addr] = \
            self.register_service(service, sta=lvap.addr)

    def handle_lvap_leave(self, lvap):
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

        self.mcast_services[mcast_addr]["schedule"] = \
            self.mcast_services[mcast_addr]["schedule"][1:] + \
            [self.mcast_services[mcast_addr]["schedule"][0]]

        phase = self.mcast_services[mcast_addr]["schedule"][0]

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

        # otherwise apply the SDN@Play algorithm
        for block in self.blocks():

            for addr, entry in self.mcast_services.items():

                # fetch txp
                if addr not in block.tx_policies:
                    block.tx_policies[addr] = TxPolicy(addr, block)

                txp = block.tx_policies[addr]

                if self.mcast_policy == TX_MCAST_DMS_H:
                    txp.mcast = TX_MCAST_DMS
                    continue

                if self.mcast_policy == TX_MCAST_LEGACY_H:
                    txp.mcast = TX_MCAST_LEGACY
                    continue

                phase = self.get_next_group_phase(addr)

                self.log.info("Mcast phase %s for group %s",
                              TX_MCAST[phase], addr)

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

        out['schedule'] = [TX_MCAST[x] for x in self.schedule]
        out['mcast_services'] = self.mcast_services

        return out


def launch(context, service_id, mcast_policy, every=EVERY):
    """ Initialize the module. """

    return Mcast(context=context, service_id=service_id,
                 mcast_policy=mcast_policy, every=every)
