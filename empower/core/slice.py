#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""EmPOWER Slice Class."""

import json

from empower.datatypes.dscp import DSCP
from empower.datatypes.etheraddress import EtherAddress

import empower.logger

LTE_SLICE_SCHED = {
    'ROUND_ROBIN_UE_SCHED': 0x80000001,
    'MULTI_SLICE_SCHED': 0x00000001
}

WIFI_SLICE_SCHED = {
    'DEFICIT_ROUND_ROBIN': 0x00000000,
    'BITRATE_FAIRNESS': 0x00000001
}


class Slice:
    """The EmPOWER slice class.

    A slice is defined starting from a JSON descriptor like the following:

    {
        "version": 1.0,
        "dscp": "0x42",
        "wifi": {
            "static-properties": {
              "amsdu_aggregation": true,
              "quantum": 12000,
              "scheduler": 0
            }
        },
        "lte": {
            "static-properties": {
              "rbgs": 5,
              "sched_id": 1
            }
        }
    }

    The descriptor above will create a slice with id 0x42 on every WiFi and LTE
    node in the network.

    In some cases it may be required to use different slice parameters only on
    certain nodes. This can be done using a descriptor like the following:

    {
        "version": 1.0,
        "dscp": "0x42",
        "wifi": {
            "static-properties": {
              "amsdu_aggregation": true,
              "quantum": 12000,
              "scheduler":0
            },
            "wtps": {
              "00:0D:B9:2F:56:64": {
                "static-properties": {
                  "quantum": 15000
                }
              }
            }
        },
        "lte": {
            "static-properties": {
              "rbgs": 5,
              "sched_id": 1
            },
            "vbses": {
                "aa:bb:cc:dd:ee:ff": {
                    "static-properties": {
                      "rbgs": 2
                    },
                }
            }
        }
    }

    In this case the slice is still created on all the nodes in the network,
    but some slice parameters are different for the specified nodes.

    The scheduler indicates the way the stations are given the resources within
    a slice. 0 corresponds to a Deficit Round Robin policy, 1 to bitrate fairness.
    """

    def __init__(self, dscp, tenant, descriptor):

        self.log = empower.logger.get_logger()

        self.dscp = DSCP(dscp)
        self.tenant = tenant

        self.wifi = {
            'static-properties': {
                'amsdu_aggregation': False,
                'quantum': 12000,
                'scheduler': WIFI_SLICE_SCHED['DEFICIT_ROUND_ROBIN']
            },
            'wtps': {}
        }

        if 'wifi' in descriptor:
            self.__parse_wifi_descriptor(descriptor)

        self.lte = {
            'static-properties': {
                'sched_id': LTE_SLICE_SCHED['ROUND_ROBIN_UE_SCHED'],
                'rbgs': 6,
                'window': 1,
                'period': 1
            },
            'vbses': {}
        }

        if 'lte' in descriptor:
            self.__parse_lte_descriptor(descriptor)

    def __parse_wifi_descriptor(self, descriptor):

        if 'static-properties' in descriptor['wifi']:
            self.__parse_wifi_static_properties(descriptor)

        if 'wtps' in descriptor['wifi']:
            self.__parse_wtps_descriptor(descriptor)

    def __parse_wifi_static_properties(self, descriptor):

        if 'amsdu_aggregation' in descriptor['wifi']['static-properties']:

            amsdu_aggregation = \
                descriptor['wifi']['static-properties']['amsdu_aggregation']

            if not isinstance(amsdu_aggregation, bool):
                amsdu_aggregation = json.loads(amsdu_aggregation.lower())

            self.wifi['static-properties']['amsdu_aggregation'] = amsdu_aggregation

        if 'quantum' in descriptor['wifi']['static-properties']:

            quantum = descriptor['wifi']['static-properties']['quantum']

            if isinstance(quantum, int):
                self.wifi['static-properties']['quantum'] = quantum
            else:
                self.wifi['static-properties']['quantum'] = int(quantum)

        if 'scheduler' in descriptor['wifi']['static-properties']:

            scheduler = \
                descriptor['wifi']['static-properties']['scheduler']

            if not isinstance(scheduler, int):
                scheduler = int(scheduler)

            if scheduler not in WIFI_SLICE_SCHED.values():
                raise ValueError("Invalid Wi-Fi slice scheduler")

            self.wifi['static-properties']['scheduler'] = scheduler

    def __parse_wtps_descriptor(self, descriptor):

        for addr in descriptor['wifi']['wtps']:

            wtp_addr = EtherAddress(addr)

            if wtp_addr not in self.tenant.wtps:
                raise KeyError("Unable to find WTP %s" % addr)

            if 'static-properties' in descriptor['wifi']['wtps'][addr]:

                self.wifi['wtps'][wtp_addr] = {'static-properties': {}}

                if 'amsdu_aggregation' in \
                    descriptor['wifi']['wtps'][addr]['static-properties']:

                    amsdu_aggregation = descriptor['wifi']['wtps'][addr] \
                        ['static-properties']['amsdu_aggregation']

                    props = self.wifi['wtps'][wtp_addr]['static-properties']

                    if not isinstance(amsdu_aggregation, bool):
                        amsdu_aggregation = json.loads(amsdu_aggregation.lower())

                    props['amsdu_aggregation'] = amsdu_aggregation

                if 'quantum' in \
                    descriptor['wifi']['wtps'][addr]['static-properties']:

                    quantum = \
                        descriptor['wifi']['wtps'][addr]['static-properties'] \
                            ['quantum']

                    if not isinstance(quantum, int):
                        quantum = int(quantum)

                    self.wifi['wtps'][wtp_addr]['static-properties']['quantum'] = quantum

                if 'scheduler' in \
                    descriptor['wifi']['wtps'][addr]['static-properties']:

                    scheduler = descriptor['wifi']['wtps'][addr] \
                        ['static-properties']['scheduler']

                    props = self.wifi['wtps'][wtp_addr]['static-properties']

                    if not isinstance(scheduler, int):
                        scheduler = int(scheduler)

                    if scheduler not in WIFI_SLICE_SCHED.values():
                        raise ValueError("Invalid Wi-Fi slice scheduler")

                    props['scheduler'] = scheduler

    def __parse_lte_descriptor(self, descriptor):

        if not self.tenant.plmn_id:
            self.log.info('Tenant %s without PLMIND', self.tenant.tenant_name)
            return

        if 'static-properties' in descriptor['lte']:
            self.__parse_lte_static_properties(descriptor)

        if 'vbses' in descriptor['lte']:
            self.__parse_vbses_descriptor(descriptor)

    def __parse_lte_static_properties(self, descriptor):

        if 'sched_id' in descriptor['lte']['static-properties']:

            sched_id = descriptor['lte']['static-properties']['sched_id']

            if not isinstance(sched_id, int):
                sched_id = int(sched_id)

            if sched_id not in LTE_SLICE_SCHED.values():
                raise ValueError("Invalid LTE slice scheduler")

            self.lte['static-properties']['sched_id'] = sched_id

        if 'rbgs' in descriptor['lte']['static-properties']:

            rbgs = descriptor['lte']['static-properties']['rbgs']

            if not isinstance(rbgs, int):
                rbgs = int(rbgs)

            self.lte['static-properties']['rbgs'] = rbgs

        if 'window' in descriptor['lte']['static-properties']:

            window = descriptor['lte']['static-properties']['window']

            if not isinstance(window, int):
                window = int(window)

            self.lte['static-properties']['window'] = window

        if 'period' in descriptor['lte']['static-properties']:

            period = descriptor['lte']['static-properties']['period']

            if not isinstance(period, int):
                period = int(period)

            self.lte['static-properties']['period'] = period

    def __parse_vbses_descriptor(self, descriptor):

        for addr in descriptor['lte']['vbses']:

            vbs_addr = EtherAddress(addr)

            if vbs_addr not in self.tenant.vbses:
                raise KeyError("Unable to find VBS %s" % addr)

            self.lte['vbses'][vbs_addr] = {
                'static-properties': {}
            }

            if 'static-properties' in descriptor['lte']['vbses'][addr]:

                if 'sched_id' in \
                    descriptor['lte']['vbses'][addr]['static-properties']:

                    sched_id = descriptor['lte']['vbses'][addr] \
                        ['static-properties']['sched_id']

                    if not isinstance(sched_id, int):
                        sched_id = int(sched_id)

                    if sched_id not in LTE_SLICE_SCHED.values():
                        raise ValueError("Invalid LTE slice scheduler")

                    self.lte['vbses'][vbs_addr]['static-properties']['sched_id'] = sched_id

                if 'rbgs' in \
                    descriptor['lte']['vbses'][addr]['static-properties']:

                    rbgs = descriptor['lte']['vbses'][addr] \
                        ['static-properties']['rbgs']

                    if not isinstance(rbgs, int):
                        rbgs = int(rbgs)

                    self.lte['vbses'][vbs_addr]['static-properties']['rbgs'] = rbgs

                if 'window' in \
                    descriptor['lte']['vbses'][addr]['static-properties']:

                    window = descriptor['lte']['vbses'][addr] \
                        ['static-properties']['window']

                    if not isinstance(window, int):
                        int(window)

                    self.lte['vbses'][vbs_addr]['static-properties']['window'] = window

                if 'period' in \
                    descriptor['lte']['vbses'][addr]['static-properties']:

                    period = descriptor['lte']['vbses'][addr] \
                        ['static-properties']['period']

                    if not isinstance(period, int):
                        period = int(period)

                    self.lte['vbses'][vbs_addr]['static-properties']['period'] = period

    def __repr__(self):
        return "%s:%s" % (self.tenant.tenant_name, self.dscp)

    def print_descriptor(self, desc):
        """ Return a JSON-serializable dictionary of a Slice descriptor """

        if isinstance(desc, dict):
            result = \
                {str(k): self.print_descriptor(v) for k, v in desc.items()}
        else:
            result = str(desc)

        return result

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Slice """

        desc = {
            'dscp': self.dscp,
            'tenant_id': self.tenant.tenant_id,
            'wifi': self.print_descriptor(self.wifi),
            'lte': self.print_descriptor(self.lte),
        }

        return desc
