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


REQ = {
  "version": "1.0",
  "stats_request_config": {
    "report_type": "complete",
    "report_frequency": "once",
    "timer_xid": 4,
    "periodicity": 6000,
    "report_config": {
      "ue_report_type": {
        "ue_report_flags": ["buffer_status_report", "power_headroom_report"],
        "ue_rnti": []
      },
      "cell_report_type": {
        "cell_report_flags": ["noise_interference"],
        "cc_id": [0]
      }
    }
  }
}

class VBSMacStatsPoller(EmpowerApp):
    """VBS Mac Stats Poller Apps.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.pollers.lvapstatspoller \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.vbspup(callback=self.vbsp_up_callback)

    def vbsp_up_callback(self, vbsp):
        """ New LVAP. """

        self.vbsp_mac_stats(vbsp=vbsp.addr, every=self.every,
                            mac_stats_req=REQ,
                            callback=self.mac_stats_callback)

    def mac_stats_callback(self, stats):
        """ New stats available. """

        self.log.info("New lvap stats received from %s" % stats.vbsp)

        print(stats.to_dict())


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return VBSMacStatsPoller(tenant_id=tenant_id, every=every)
