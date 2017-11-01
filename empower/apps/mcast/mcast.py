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

"""Simple multicast management app."""

from empower.core.app import EmpowerApp
from empower.core.resourcepool import BT_HT20
from empower.core.resourcepool import TX_MCAST
from empower.core.resourcepool import TX_MCAST_DMS
from empower.core.resourcepool import TX_MCAST_LEGACY
from empower.datatypes.etheraddress import EtherAddress
from empower.apps.mcast.mcastclient import MCastClientInfo


class MCastManager(EmpowerApp):
    """Multicast app with rate adaptation support.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.mcast.mcast \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada00

    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # app parameters
        self.prob_thershold = 90.0
        self.mcast_addr = EtherAddress("01:00:5e:00:c8:dd")
        self.current = 0
        self.dms = 1
        self.legacy = 4
        self.schedule = [TX_MCAST_DMS] * self.dms + \
            [TX_MCAST_LEGACY] * self.legacy

        # register lvap join/leave events
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)

    def lvap_join_callback(self, lvap):
        """Called when a new LVAP joins the network."""

        self.mcast_clients[lvap.addr] = \
            self.lvap_stats(lvap=lvap.addr, every=self.every)

    def lvap_leave_callback(self, lvap):
        """Called when an LVAP leaves the network."""

        del self.mcast_clients[lvap.addr]

    def get_next_mode(self):
        """Get next mcast mode in the schedule."""

        mode = self.schedule[self.current % len(self.schedule)]
        self.current += 1

        return mode

    def loop(self):
        """ Periodic job. """

        mode = self.get_next_mode()
        self.log.info("Mcast mode %s", TX_MCAST[mode])

        for block in self.blocks():

            # fetch txp
            txp = block.tx_policies[self.mcast_addr]

            # no clients or DMS slot
            if not self.lvaps(block) or mode == TX_MCAST_DMS:
                self.log.info("Block %s setting mcast address %s to %s",
                              block, self.mcast_addr, TX_MCAST[TX_MCAST_DMS])
                txp.mcast = TX_MCAST_DMS
                continue

            # legacy period
            mcs_type = BT_HT20

            # compute MCS
            mcs = 0

            # assign MCS
            self.info("Block %s setting mcast address %s to %s",
                      block, self.mcast_addr, TX_MCAST[TX_MCAST_DMS])
            txp.mcast = TX_MCAST_LEGACY
            if mcs_type == BT_HT20:
                txp.ht_mcs = [mcs]
            else:
                txp.mcs = [mcs]

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['schedule'] = [TX_MCAST[x] for x in self.schedule]
        out['mcast_clients'] = \
            {str(k): v for k, v in self.mcast_clients.items()}

        return out


def launch(tenant_id, every=1000):
    """ Initialize the module. """

    return MCastManager(tenant_id=tenant_id, every=every)
