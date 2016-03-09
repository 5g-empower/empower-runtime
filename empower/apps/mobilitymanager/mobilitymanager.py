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

from empower.datatypes.etheraddress import EtherAddress
from empower.core.app import EmpowerApp
from empower.core.app import EmpowerAppHandler
from empower.core.app import EmpowerAppHomeHandler
from empower.core.app import DEFAULT_PERIOD
from empower.core.resourcepool import ResourcePool
from empower.triggers.rssi import rssi
from empower.events.wtpup import wtpup
from empower.maps.ucqm import ucqm

import empower.logger
LOG = empower.logger.get_logger()


DEFAULT_LIMIT = -99


def handover(lvap, wtps):
    """ Handover the LVAP to a WTP with
    an RSSI higher that -65dB. """

    # Initialize the Resource Pool
    pool = ResourcePool()

    # Update the Resource Pool with all
    # the available Resourse Blocks
    for wtp in wtps:
        pool = pool | wtp.supports

    # Select matching Resource Blocks
    matches = pool & lvap.scheduled_on

    # Filter Resource Blocks by RSSI
    valid = [block for block in matches
             if block.ucqm[lvap.addr]['ewma_rssi'] >= -55]

    # Perform the handover
    new_block = valid.pop() if valid else None
    LOG.info("LVAP %s setting new block %s" % (lvap.addr, new_block))
    lvap.scheduled_on = new_block

    # Set port
    for block in lvap.scheduled_on:
        port = lvap.scheduled_on[block]
        port.no_ack = True
        port.tx_power = 20
        port.rts_cts = 3500
        port.mcs = [6, 12]


class MobilityManagerHandler(EmpowerAppHandler):
    pass


class MobilityManagerHomeHandler(EmpowerAppHomeHandler):
    pass


class MobilityManager(EmpowerApp):
    """Basic mobility manager.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.mobilitymanager.mobilitymanager:$ID

    """

    MODULE_NAME = "mobilitymanager"
    MODULE_HANDLER = MobilityManagerHandler
    MODULE_HOME_HANDLER = MobilityManagerHomeHandler

    def __init__(self, tenant, **kwargs):

        self.__limit = DEFAULT_LIMIT

        EmpowerApp.__init__(self, tenant, **kwargs)

        # Register an RSSI trigger for all LVAPs
        rssi(lvaps="ff:ff:ff:ff:ff:ff",
             tenant_id=self.tenant.tenant_id,
             relation='LT',
             value=self.limit,
             callback=self.low_rssi)

        # Register an wtp up event
        wtpup(tenant_id=self.tenant.tenant_id, callback=self.wtp_up_callback)

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

        LOG.info("Setting limit %u dB" % value)
        self.__limit = limit

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        for block in wtp.supports:

            if block.black_listed:
                continue

            ucqm(tenant_id=self.tenant.tenant_id,
                 block=block,
                 every=self.every)

    def low_rssi(self, trigger):
        """ Perform handover if an LVAP's rssi is
        going below the threshold. """

        lvap_addr = EtherAddress(trigger.events[-1]['lvap'])
        handover(self.lvap(lvap_addr), self.wtps())

    def loop(self):
        """ Periodic job. """

        # Handover every active LVAP to
        # the best WTP
        for lvap in self.lvaps():
            handover(lvap, self.wtps())


def launch(tenant, limit=DEFAULT_LIMIT, period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return MobilityManager(tenant, every=period, limit=limit)
