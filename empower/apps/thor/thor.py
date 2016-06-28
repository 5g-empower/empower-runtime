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
from empower.core.app import DEFAULT_PERIOD


class Thor(EmpowerApp):
    """Energy consumption balacing app.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)
        max_lvap_per_wtp: max number of LVAPs per WTP (optional, default 2)

    Example:

        ./empower-runtime.py apps.thor.thor \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D

    """

    def __init__(self, **kwargs):
        self.__max_lvaps_per_wtp = 2
        self.__idle_cycles = {}
        EmpowerApp.__init__(self, **kwargs)

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

        self.log.info("Setting max_lvaps_per_wtp to %u" % value)
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
                self.log.info("LVAP %s on WTP w/o feed, ignoring.", lvap.addr)
                continue
            if not tank:
                tank = [v for v in self.wtps() if v.feed and v.connection]
            wtp = tank.pop()
            lvap.wtp = wtp
            mappings[lvap.wtp].append(lvap)
            self.log.info("LVAP %s -> %s", lvap.addr, lvap.wtp)
            if not always_on:
                always_on = lvap.wtp

        for wtp in mappings:
            if len(mappings[wtp]) > self.max_lvaps_per_wtp:
                count = count + (len(mappings[wtp]) - self.max_lvaps_per_wtp)

        if not always_on:
            always_on = [x for x in self.wtps() if x.feed][0]

        self.log.info("WTP %s always on", always_on.addr)

        for wtp in mappings:
            if wtp == always_on or len(mappings[wtp]) > 0:
                if wtp in self.__idle_cycles:
                    del self.__idle_cycles[wtp]
                wtp.powerup()
            elif count > 0:
                if wtp in self.__idle_cycles:
                    del self.__idle_cycles[wtp]
                wtp.powerup()
                count = count - 1
            elif wtp.feed.is_on:
                if wtp not in self.__idle_cycles:
                    self.__idle_cycles[wtp] = 0
                self.log.info("WTP %s idle for %u cycles", wtp.addr,
                              self.__idle_cycles[wtp])
                if self.__idle_cycles[wtp] >= 5:
                    del self.__idle_cycles[wtp]
                    wtp.powerdown()
                else:
                    self.__idle_cycles[wtp] = self.__idle_cycles[wtp] + 1


def launch(tenant_id, max_lvaps_per_wtp=2, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return Thor(tenant_id=tenant_id, max_lvaps_per_wtp=max_lvaps_per_wtp,
                every=every)
