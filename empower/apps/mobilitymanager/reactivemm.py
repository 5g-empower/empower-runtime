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

"""Proactive mobility manager."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


DEFAULT_LIMIT = -30


class ReactiveMobilityManager(EmpowerApp):
    """Proactive mobility manager.

    Command Line Parameters:

        tenant_id: tenant id
        limit: handover limit in dBm (optional, default -80)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.mobilitymanager.reactivemm \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26
    """

    def __init__(self, **kwargs):

        EmpowerApp.__init__(self, **kwargs)

        self.__limit = DEFAULT_LIMIT

        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        # Start polling the WTP
        for block in wtp.supports:
            self.ucqm(block=block, every=self.every)

    def lvap_join_callback(self, lvap):
        """Called when an joins the network."""

        self.rssi(lvap=lvap.addr,
                  value=self.limit,
                  relation='LT',
                  callback=self.low_rssi)

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

        lvap.blocks = self.blocks().sortByRssi(lvap.addr).first()


def launch(tenant_id, limit=DEFAULT_LIMIT, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return ReactiveMobilityManager(tenant_id=tenant_id,
                                   limit=limit,
                                   every=every)
