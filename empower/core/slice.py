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


class Slice:
    """The base EmPOWER slice class.

    A slice is defined starting from the following descriptor (in JSON format)

    {
        "version" : 1.0,
        "dscp": "0x42"
        "wifi-properties": {
            "amsdu_aggregation": true
        },
        "wtps": {
            "00:01:02:03:04:05": {
                "quantum": 12000
            }
        },
        "lte-properties": {},
        "vbses": {
            "aa:bb:cc:dd:ee:ff": {
                "prbs": 4
            }
        }
    }

    Attributes:
    """

    def __init__(self, dscp, tenant, descriptor):

        self.dscp = DSCP(dscp)
        self.tenant = tenant

        self.wifi_properties = {}

        if 'wifi-properties' in descriptor:

            if 'amsdu_aggregation' in descriptor['wifi-properties']:

                amsdu_aggregation = \
                    descriptor['wifi-properties']['amsdu_aggregation']

                if isinstance(amsdu_aggregation, bool):
                    self.wifi_properties['amsdu_aggregation'] = \
                        amsdu_aggregation
                else:
                    self.wifi_properties['amsdu_aggregation'] = \
                        json.loads(amsdu_aggregation.lower())

        self.lte_properties = {}

        self.wtps = {}

        if 'wtps' in descriptor:

            for addr in descriptor['wtps']:

                wtp_addr = EtherAddress(addr)

                if wtp_addr not in self.tenant.wtps:
                    raise KeyError("Unable to find WTP %s" % addr)

                self.wtps[wtp_addr] = {'properties': {}, 'blocks': {}}

                if 'quantum' in descriptor['wtps'][addr]:

                    quantum = descriptor['wtps'][addr]['quantum']

                    if isinstance(amsdu_aggregation, int):
                        self.wtps[wtp_addr]['properties']['quantum'] = quantum
                    else:
                        self.wtps[wtp_addr]['properties']['quantum'] = \
                            int(quantum)

        self.vbses = {}

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Slice """

        desc = {
            'dscp': self.dscp,
            'tenant_id': self.tenant.tenant_id,
            'wifi-properties': self.wifi_properties,
            'lte-properties': self.lte_properties,
            'wtps': {str(k): v for k, v in self.wtps.items()},
            'vbses': {str(k): v for k, v in self.vbses.items()},
        }

        return desc
