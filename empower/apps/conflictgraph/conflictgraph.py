#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
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

"""Channel Quality and Conflict Maps visulization app."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class ConflictGraph(EmpowerApp):
    """Channel Quality and Conflict Maps visulization app.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.pollers.linkstatspoller --tenant_id=$ID

    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.conflicts = {'networks': [], 'stations': []}
        self.wtpup(callback=self.wtp_up_callback)

    def to_dict(self):

        out = super().to_dict()
        out['conflicts'] = self.conflicts
        return out

    def wtp_up_callback(self, wtp):
        """ Called when a new WTP connects to the controller"""

        for block in wtp.supports:

            self.ucqm(block=block, every=self.every,
                      callback=self.update_cm)

            self.ncqm(block=block, every=self.every,
                      callback=self.update_cm)

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

                for blk in dst.scheduled_on:

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
