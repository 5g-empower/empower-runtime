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

    def __init__(self, tenant, **kwargs):

        self.__max_lvaps_per_wtp = 2
        self.idle_cycles = {}

        EmpowerApp.__init__(self, tenant, **kwargs)

    @property
    def max_lvaps_per_wtp(self):
        """Return max_lvaps_per_wtp."""

        return self.__max_lvaps_per_wtp

    @max_lvaps_per_wtp.setter
    def max_lvaps_per_wtp(self, value):
        """Set max_lvaps_per_wtp."""

        max_lvaps_per_wtp = int(value)

        if max_lvaps_per_wtp < 1:
            raise ValueError("Invalid value for max_lvaps_per_wtp")

        LOG.info("Setting max_lvaps_per_wtp to %u" % value)
        self.__max_lvaps_per_wtp = max_lvaps_per_wtp

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


def launch(tenant, max_lvaps_per_wtp=2, period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return Thor(tenant, max_lvaps_per_wtp=max_lvaps_per_wtp, every=period)
