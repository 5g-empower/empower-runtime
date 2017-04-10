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

"""LVAP Statistics Poller Apps."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class LVAPStatsPoller(EmpowerApp):
    """LVAP Stats Poller Apps.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.pollers.lvapstatspoller \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.lvapjoin(callback=self.lvap_join_callback)

    def lvap_join_callback(self, lvap):
        """ New LVAP. """

        self.lvap_stats(lvap=lvap.addr,
                        every=self.every,
                        callback=self.lvap_stats_callback)

    def lvap_stats_callback(self, counter):
        """ New stats available. """

        self.log.info("New lvap stats received from %s" % counter.lvap)


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return LVAPStatsPoller(tenant_id=tenant_id, every=every)
