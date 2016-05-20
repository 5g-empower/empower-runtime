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

"""Basic mobility manager."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD

from empower.datatypes.etheraddress import EtherAddress
from empower.core.resourcepool import ResourcePool


DEFAULT_LIMIT = -10


class MobilityManager(EmpowerApp):
    """Basic mobility manager.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.mobilitymanager.mobilitymanager:$ID

    """

    def __init__(self, **kwargs):
        self.__limit = DEFAULT_LIMIT
        EmpowerApp.__init__(self, **kwargs)

        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)

    def lvap_join_callback(self, lvap):
        """Called when a new LVAP connects the network."""

        lvap.rssi(relation='LT', value=self.limit, callback=self.low_rssi)

    def handover(self, lvap):
        """ Handover the LVAP to a WTP with
        an RSSI higher that -65dB. """

        self.log.info("Running handover...")

        # Initialize the Resource Pool
        pool = ResourcePool()

        # Update the Resource Pool with all
        # the available Resourse Blocks
        for wtp in self.wtps():
            pool = pool | wtp.supports

        # Select matching Resource Blocks
        matches = pool & lvap.scheduled_on

        # Filter Resource Blocks by RSSI
        valid = [block for block in matches
                 if block.ucqm[lvap.addr]['ewma_rssi'] >= -85]

        if not valid:
            return

        new_block = max(valid, key=lambda x: x.ucqm[lvap.addr]['ewma_rssi'])
        self.log.info("LVAP %s setting new block %s" % (lvap.addr, new_block))

        lvap.scheduled_on = new_block

        # Set port
        for block in lvap.scheduled_on:
            port = lvap.scheduled_on[block]
            port.no_ack = True
            port.rts_cts = 3500
            port.mcs = [6, 12, 54]

    @property
    def limit(self):
        """Return loop period."""

        return self.__limit

    @limit.setter
    def limit(self, value):
        """Set limit."""

        limit = int(value)

        if limit > 0 or limit < -100:
            raise ValueError("Invalid value for limit")

        self.log.info("Setting limit %u dB" % value)
        self.__limit = limit

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        for block in wtp.supports:
            self.ucqm(block=block, every=self.every)

    def low_rssi(self, trigger):
        """ Perform handover if an LVAP's rssi is
        going below the threshold. """

        print(trigger)
        return

        lvap_addr = EtherAddress(trigger.events[-1]['lvap'])
        lvap = self.lvap(lvap_addr)

        self.handover(lvap)

    def loop(self):
        """ Periodic job. """

        # Handover every active LVAP to
        # the best WTP
        for lvap in self.lvaps():
            self.handover(lvap)


def launch(tenant_id, limit=DEFAULT_LIMIT, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return MobilityManager(tenant_id=tenant_id, limit=limit, every=every)
