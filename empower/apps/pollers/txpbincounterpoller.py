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

"""TXP Bin Counters Poller App."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.datatypes.etheraddress import EtherAddress
from empower.core.resourcepool import TX_MCAST_LEGACY


class TXPBinCounterPoller(EmpowerApp):
    """TXP Bin Counters Poller App.

    Command Line Parameters:

        tenant_id: tenant id
        filepath: path to file for statistics (optional, default ./)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.pollers.txpbincounterpoller \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wtpup(callback=self.wtp_up_callback)

    def wtp_up_callback(self, wtp):
        """ New LVAP. """

        for block in wtp.supports:

            tx_policy = block.tx_policies[EtherAddress("ff:ff:ff:ff:ff:ff")]
            tx_policy.mcast = TX_MCAST_LEGACY
            tx_policy.mcs = [6]

            self.txp_bin_counter(block=block,
                                 mcast="ff:ff:ff:ff:ff:ff",
                                 callback=self.txp_bin_counter_callback)

    def txp_bin_counter_callback(self, counter):
        """Counters callback."""

        self.log.info("Mcast address %s packets %u", counter.mcast,
                      counter.tx_packets[0])


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return TXPBinCounterPoller(tenant_id=tenant_id, every=every)
