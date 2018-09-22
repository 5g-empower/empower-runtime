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
from empower.core.transmissionpolicy import TX_MCAST
from empower.core.transmissionpolicy import TX_MCAST_DMS
from empower.core.transmissionpolicy import TX_MCAST_LEGACY
from empower.datatypes.etheraddress import EtherAddress
import sys

TX_MCAST_SDNPLAY = 0x3
TX_MCAST_SDNPLAY_H = "sdnplay"


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
        self.receptors = {}
        self.receptors_mcses = {}
        self.receptors_quality = {}
        self.prob_threshold = 90.0
        self.mcast_addr = EtherAddress("01:00:5e:00:c8:dd")
        self.current = 0
        self.dms = 1
        self.legacy = 9
        self.schedule = [TX_MCAST_DMS] * self.dms + \
            [TX_MCAST_LEGACY] * self.legacy
        self._demo_mode = TX_MCAST_SDNPLAY_H
        self.status = {}

    @property
    def demo_mode(self):
        """Get demo mode."""

        return self._demo_mode

    @demo_mode.setter
    def demo_mode(self, demo_mode):
        """Set the demo mode."""

        self._demo_mode = demo_mode

        # if the demo is not SDN@Play, the tx policy should be ignored
        for block in self.blocks():
            # fetch txp
            txp = block.tx_policies[self.mcast_addr]
            if demo_mode == TX_MCAST[TX_MCAST_DMS]:
                txp.mcast = TX_MCAST_DMS
            elif demo_mode == TX_MCAST[TX_MCAST_LEGACY]:
                txp.mcast = TX_MCAST_LEGACY
                mcs_type = BT_HT20
                if mcs_type == BT_HT20:
                    txp.ht_mcs = [min(block.ht_supports)]
                else:
                    txp.mcs = [min(block.supports)]

        if demo_mode != TX_MCAST_DMSPLAY_H:
            self.status['MCS'] = "None"
            self.status['Phase'] = "None"

    def lvap_join(self, lvap):
        """Called when an LVAP joins a tenant."""

        self.receptors[lvap.addr] = \
            self.lvap_stats(lvap=lvap.addr, every=self.every)

    def lvap_leave(self, lvap):
        """Called when an LVAP leaves the network."""

        if lvap.addr in self.receptors:
            del self.receptors[lvap.addr]

        if lvap.addr in self.receptors_mcses:
            del self.receptors_mcses[lvap.addr]

        if lvap.addr in self.receptors_quality:
            del self.receptors_quality[lvap.addr]

    def compute_receptors_mcs(self):
        """ New stats available. """

        for value in self.receptors.values():
            highest_prob = 0
            information = value.to_dict()

            if not information["rates"]:
                continue

            lvap = information["lvap"]
            keys = [float(i) for i in information["rates"].keys()]
            best_mcs = min(list(map(int, keys)))

            if lvap in self.receptors_mcses:
                del self.receptors_mcses[lvap]

            self.receptors_mcses[lvap] = []

            for mcs, stats in information["rates"].items():
                if stats["prob"] >= self.prob_threshold:
                    self.receptors_mcses[lvap].append(int(float(mcs)))
                elif stats["prob"] > highest_prob:
                    best_mcs = int(float(mcs))
                    highest_prob = stats["prob"]

            if not self.receptors_mcses[lvap]:
                self.receptors_quality[lvap] = False
                self.receptors_mcses[lvap].append(best_mcs)
            else:
                self.receptors_quality[lvap] = True

    def calculate_mcs(self):

        self.compute_receptors_mcs()
        if not self.receptors_mcses:
            return 0

        if False not in self.receptors_quality.values():
            mcses = []
            for rates in self.receptors_mcses.values():
                mcses.append(rates)

            mcs_intersection = list(set.intersection(*map(set, mcses)))
            if mcs_intersection:
                mcs = max(mcs_intersection)
                return mcs

        mcs = sys.maxsize
        for rates in self.receptors_mcses.values():
            mcs = min(max(rates), mcs)

        return mcs

    def get_next_phase(self):
        """Get next mcast phase to be scheduled."""

        phase = self.schedule[self.current % len(self.schedule)]
        self.current += 1

        return phase

    def loop(self):
        """ Periodic job. """

        # if the demo is now in DMS it should not calculate anything
        if self.demo_mode == TX_MCAST[TX_MCAST_DMS] or \
           self.demo_mode == TX_MCAST[TX_MCAST_LEGACY]:
            return

        # if there are no clients the mode should be dms
        if not self.receptors:
            for block in self.blocks():
                # fetch txp
                txp = block.tx_policies[self.mcast_addr]

                if txp.mcast == TX_MCAST_DMS:
                    continue

                txp.mcast = TX_MCAST_DMS


        phase = self.get_next_phase()
        self.log.info("Mcast phase %s", TX_MCAST[phase])

        for block in self.blocks():
            # fetch txp
            txp = block.tx_policies[self.mcast_addr]

            if phase == TX_MCAST_DMS:
                txp.mcast = TX_MCAST_DMS
            else:
                # legacy period
                mcs_type = BT_HT20

                # compute MCS
                mcs = max(self.calculate_mcs(), min(block.supports))
                self.status['MCS'] = mcs
                txp.mcast = TX_MCAST_LEGACY

                if mcs_type == BT_HT20:
                    txp.ht_mcs = [mcs]
                else:
                    txp.mcs = [mcs]

                # assign MCS
                self.log.info("Block %s setting mcast address %s to %s MCS %d",
                              block, self.mcast_addr, TX_MCAST[TX_MCAST_DMS], mcs)

            self.status['Phase'] = TX_MCAST[phase]

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['Demo_mode'] = self.demo_mode
        out['SDN@Play parameters'] = \
            {str(k): v for k, v in self.status.items()}
        out['Phases_schedule'] = [TX_MCAST[x] for x in self.schedule]
        out['Receptors'] = \
            {str(k): v for k, v in self.receptors.items()}
        out['Status'] = \
            {str(k): v for k, v in self.status.items()}

        return out


def launch(tenant_id, every=1000):
    """ Initialize the module. """

    return MCastManager(tenant_id=tenant_id, every=every)
