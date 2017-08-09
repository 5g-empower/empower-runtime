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

"""Channel Quality and Conflict Maps visulization app."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class ConflictGraph(EmpowerApp):
    """Channel Quality and Conflict Maps visulization app.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.pollers.linkstatspoller \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.conflicts = {'networks': [], 'stations': []}
        self.wtpup(callback=self.wtp_up_callback)

    def to_dict(self):
        """Return json-serializable representation of the object."""

        out = super().to_dict()
        out['conflicts'] = self.conflicts
        return out

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        for block in wtp.supports:
            self.ucqm(block=block, every=self.every, callback=self.update_cm)
            self.ncqm(block=block, every=self.every, callback=self.update_cm)

    def update_cm(self, _):
        """Periodic job."""

        # Initialize conflict map
        self.conflicts = {'networks': [], 'stations': []}

        # Interate over all the (directed) LVAPs
        # pairs in the network
        for src in self.lvaps():
            for dst in self.lvaps():

                # Ignore links to self
                if src == dst:
                    continue

                # If the receiver of this link is within
                # interference range of the transmitter
                # of the other link, then add an entry
                # in the conflict map (for both clients
                # and access points)

                for blk in dst.blocks:

                    if src.addr in blk.ucqm:

                        self.log.info("(%s, %s) -> (%s, %s)",
                                      src.addr, src.wtp,
                                      dst.addr, dst.wtp)
                        self.conflicts['stations'].append((src, dst))

                    if src.lvap_bssid in blk.ncqm or \
                       src.wtp == dst.wtp:

                        self.log.info("(%s, %s) -> (%s, %s)",
                                      src.addr, src.wtp,
                                      dst.addr, dst.wtp)
                        self.conflicts['networks'].append((src, dst))


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return ConflictGraph(tenant_id=tenant_id, every=every)
