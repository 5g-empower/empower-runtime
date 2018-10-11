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


class Slice:
    """The base EmPOWER slice class.

    A slice is defined starting from the following descriptor (in JSON format).
    Notice how any slice properties can be overridded on a per node-basis.

    {
        "version": 1.0,
        "dscp": "0x42",
        "wifi": {
            "static-properties": {
              "amsdu_aggregation": true,
              "quantum": 12000
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
            "runtime-properties": {
              "rntis": [
                12345,
                22233
              ]
            },
            "vbses": {
                "aa:bb:cc:dd:ee:ff": {
                    "static-properties": {
                      "rbgs": 2
                    },
                    "runtime-properties": {
                      "rntis": [
                        555555
                      ]
                    },
                    "cells": {
                    }
                }
            }
        }
    }
    """

    def __init__(self, dscp, tenant, descriptor):

        self.log = empower.logger.get_logger()

        self.dscp = DSCP(dscp)
        self.tenant = tenant

        self.wifi = {
            'static-properties': {
                'amsdu_aggregation': False,
                'quantum': 12000
            },
            'wtps': {}
        }

        if 'wifi' in descriptor:
            self.__parse_wifi_descriptor(descriptor)

        self.lte = {
            'static-properties': {
                'sched_id': 0,
                'rbgs': 6
            },
            'runtime-properties': {
                'rntis': []
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

            if isinstance(amsdu_aggregation, bool):
                self.wifi['static-properties']['amsdu_aggregation'] = \
                    amsdu_aggregation
            else:
                self.wifi['static-properties']['amsdu_aggregation'] = \
                    json.loads(amsdu_aggregation.lower())

        if 'quantum' in descriptor['wifi']['static-properties']:

            quantum = descriptor['wifi']['static-properties']['quantum']

            if isinstance(amsdu_aggregation, int):
                self.wifi['static-properties']['quantum'] = quantum
            else:
                self.wifi['static-properties']['quantum'] = int(quantum)

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

                    if isinstance(amsdu_aggregation, bool):
                        props['amsdu_aggregation'] = amsdu_aggregation
                    else:
                        props['amsdu_aggregation'] = \
                            json.loads(amsdu_aggregation.lower())

                if 'quantum' in \
                    descriptor['wifi']['wtps'][addr]['static-properties']:

                    quantum = \
                        descriptor['wifi']['wtps'][addr]['static-properties'] \
                            ['quantum']

                    if isinstance(quantum, int):
                        self.wifi['wtps'][wtp_addr]['static-properties'] \
                            ['quantum'] = quantum
                    else:
                        self.wifi['wtps'][wtp_addr]['static-properties'] \
                        ['quantum'] = int(quantum)

            if 'blocks' in descriptor['wifi']['wtps'][addr]:
                self.wifi['wtps'][wtp_addr]['blocks'] = \
                    descriptor['wifi']['wtps'][addr]['blocks']

    def __parse_lte_descriptor(self, descriptor):

        if not self.tenant.plmn_id:
            self.log.info('Tenant %s without PLMIND', self.tenant.tenant_name)
            return

        if 'static-properties' in descriptor['lte']:
            self.__parse_lte_static_properties(descriptor)

        if 'runtime-properties' in descriptor['lte']:
            self.__parse_lte_runtime_descriptor(descriptor)

        if 'vbses' in descriptor['lte']:
            self.__parse_vbses_descriptor(descriptor)

    def __parse_lte_static_properties(self, descriptor):

        if 'sched_id' in descriptor['lte']['static-properties']:

            sched_id = descriptor['lte']['static-properties']['sched_id']

            if isinstance(sched_id, int):
                self.lte['static-properties']['sched_id'] = sched_id
            else:
                self.lte['static-properties']['sched_id'] = int(sched_id)

        if 'rbgs' in descriptor['lte']['static-properties']:

            rbgs = descriptor['lte']['static-properties']['rbgs']

            if isinstance(rbgs, int):
                self.lte['static-properties']['rbgs'] = rbgs
            else:
                self.lte['static-properties']['rbgs'] = int(rbgs)

    def __parse_lte_runtime_descriptor(self, descriptor):

        if 'rntis' in descriptor['lte']['runtime-properties']:

            rntis = descriptor['lte']['runtime-properties']['rntis']

            if isinstance(rntis, list):
                self.lte['runtime-properties']['rntis'] = \
                    [int(x) for x in rntis]
            else:
                self.lte['runtime-properties']['rntis'] = [int(rntis)]

    def __parse_vbses_descriptor(self, descriptor):

        for addr in descriptor['lte']['vbses']:

            vbs_addr = EtherAddress(addr)

            if vbs_addr not in self.tenant.vbses:
                raise KeyError("Unable to find VBS %s" % addr)

            self.lte['vbses'][vbs_addr] = \
                {'static-properties': {},
                 'runtime-properties': {},
                 'cells': {}}

            if 'static-properties' in descriptor['lte']['vbses'][addr]:

                if 'sched_id' in \
                    descriptor['lte']['vbses'][addr]['static-properties']:

                    sched_id = descriptor['lte']['vbses'][addr] \
                        ['static-properties']['sched_id']

                    if isinstance(sched_id, int):
                        self.lte['vbses'][vbs_addr]['static-properties'] \
                        ['sched_id'] = sched_id
                    else:
                        self.lte['vbses'][vbs_addr]['static-properties'] \
                        ['sched_id'] = int(sched_id)

                if 'rbgs' in \
                    descriptor['lte']['vbses'][addr]['static-properties']:

                    rbgs = descriptor['lte']['vbses'][addr] \
                        ['static-properties']['rbgs']

                    if isinstance(rbgs, int):
                        self.lte['vbses'][vbs_addr]['static-properties'] \
                            ['rbgs'] = rbgs
                    else:
                        self.lte['vbses'][vbs_addr]['static-properties'] \
                            ['rbgs'] = int(rbgs)

            if 'runtime-properties' in descriptor['lte']['vbses'][addr]:

                if 'rntis' in \
                    descriptor['lte']['vbses'][addr]['runtime-properties']:

                    rntis = descriptor['lte']['vbses'][addr] \
                        ['runtime-properties']['rntis']

                    if isinstance(rntis, list):
                        self.lte['vbses'][vbs_addr]['runtime-properties'] \
                        ['rntis'] = [int(x) for x in rntis]
                    else:
                        self.lte['vbses'][vbs_addr]['runtime-properties'] \
                        ['rntis'] = [int(rntis)]

            if 'cells' in descriptor['lte']['vbses'][addr]:
                self.lte['vbses'][vbs_addr]['cells'] = \
                    descriptor['lte']['vbses'][addr]['cells']

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
