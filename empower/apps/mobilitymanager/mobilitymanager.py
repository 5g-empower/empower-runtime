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

"""Basic mobility manager."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


DEFAULT_LIMIT = -30


class MobilityManager(EmpowerApp):
    """Basic mobility manager.

    Command Line Parameters:

        tenant_id: tenant id
        limit: handover limit in dBm (optional, default -80)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.mobilitymanager.mobilitymanager \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26
    """

    def __init__(self, **kwargs):
        self.__limit = DEFAULT_LIMIT
        EmpowerApp.__init__(self, **kwargs)

        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        for block in wtp.supports:

            self.ucqm(block=block, every=self.every)

            self.busyness_trigger(value=10,
                                  relation='GT',
                                  block=block,
                                  callback=self.high_occupancy)

    def lvap_join_callback(self, lvap):
        """Called when an joins the network."""

        self.rssi(lvap=lvap.addr,
                  value=self.limit,
                  relation='LT',
                  callback=self.low_rssi)

    def high_occupancy(self, trigger):
        """Call when channel is too busy."""

        self.log.info("Block %s busyness %f" %
                      (trigger.block, trigger.event['current']))

    def handover(self, lvap):
        """ Handover the LVAP to a WTP with
        an RSSI higher that -65dB. """

        self.log.info("Running handover...")

        pool = self.blocks()
        matches = pool & lvap.supported

        if not matches:
            return

        valid = [block for block in matches
                 if block.ucqm[lvap.addr]['mov_rssi'] >= self.limit]

        if not valid:
            return

        new_block = max(valid, key=lambda x: x.ucqm[lvap.addr]['mov_rssi'])
        self.log.info("LVAP %s setting new block %s" % (lvap.addr, new_block))

        lvap.scheduled_on = new_block

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

    def low_rssi(self, trigger):
        """ Perform handover if an LVAP's rssi is
        going below the threshold. """

        self.log.info("Received trigger from %s rssi %u dB",
                      trigger.event['block'],
                      trigger.event['current'])

        lvap = self.lvap(trigger.lvap)

        if not lvap:
            return

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
