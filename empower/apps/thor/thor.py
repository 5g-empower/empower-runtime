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

"""Energy consumption balacing app."""

from empower.core.app import EmpowerApp
from empower.core.app import EmpowerAppHandler
from empower.core.app import EmpowerAppHomeHandler
from empower.core.app import DEFAULT_PERIOD

import empower.logger
LOG = empower.logger.get_logger()


class ThorHandler(EmpowerAppHandler):
    pass


class ThorHomeHandler(EmpowerAppHomeHandler):
    pass


class Thor(EmpowerApp):
    """Energy consumption balacing app.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)
        max_lvap_per_wtp: max number of LVAPs per WTP (optional, default 2)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.thor.thor:$ID --max_lvaps_per_wtp=2

    """

    MODULE_NAME = "thor"
    MODULE_HANDLER = ThorHandler
    MODULE_HOME_HANDLER = ThorHomeHandler

    def __init__(self, tenant, period=None, max_lvaps_per_wtp=2):

        EmpowerApp.__init__(self, tenant, period)
        self.max_lvaps_per_wtp = int(max_lvaps_per_wtp)
        self.idle_cycles = {}

    def loop(self):
        """ Periodic job. """

        count = 0
        mappings = {v: [] for v in self.wtps() if v.feed}
        tank = [v for v in self.wtps()
                for _ in range(self.max_lvaps_per_wtp)
                if v.feed and v.connection]

        always_on = None

        if not tank:
            return

        for lvap in self.lvaps():
            if not lvap.wtp.feed:
                LOG.info("LVAP %s on WTP w/o feed, ignoring.", lvap.addr)
                continue
            if not tank:
                tank = [v for v in self.wtps() if v.feed and v.connection]
            wtp = tank.pop()
            lvap.wtp = wtp
            mappings[lvap.wtp].append(lvap)
            LOG.info("LVAP %s -> %s", lvap.addr, lvap.wtp)
            if not always_on:
                always_on = lvap.wtp

        for wtp in mappings:
            if len(mappings[wtp]) > self.max_lvaps_per_wtp:
                count = count + (len(mappings[wtp]) - self.max_lvaps_per_wtp)

        if not always_on:
            always_on = [x for x in self.wtps() if x.feed][0]

        LOG.info("WTP %s always on", always_on.addr)
        LOG.info("Number of APs to be powered on %u", count)

        for wtp in mappings:

            if wtp == always_on or len(mappings[wtp]) > 0:
                if wtp in self.idle_cycles:
                    del self.idle_cycles[wtp]
                wtp.powerup()
            elif count > 0:
                if wtp in self.idle_cycles:
                    del self.idle_cycles[wtp]
                wtp.powerup()
                count = count - 1
            elif wtp.feed.is_on:
                if wtp not in self.idle_cycles:
                    self.idle_cycles[wtp] = 0
                LOG.info("WTP %s idle for %u cycles", wtp.addr,
                         self.idle_cycles[wtp])
                if self.idle_cycles[wtp] >= 5:
                    del self.idle_cycles[wtp]
                    wtp.powerdown()
                else:
                    self.idle_cycles[wtp] = self.idle_cycles[wtp] + 1


def launch(tenant, period=DEFAULT_PERIOD, max_lvaps_per_wtp=2):
    """ Initialize the module. """

    return Thor(tenant, period, max_lvaps_per_wtp)
