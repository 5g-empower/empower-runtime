#!/usr/bin/env python3
#
# Copyright (c) 2018 Roberto Riggio
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

"""WTP Bin counter Poller Apps."""

from empower.core.app import EmpowerApp


class WTPBinCounterPoller(EmpowerApp):
    """WTP Bin Counter Poller Apps.

    Command Line Parameters:
        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:
        ./empower-runtime.py apps.pollers.counterspoller \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def wtp_up(self, wtp):
        """New WTP."""

        self.wtp_bin_counter(wtp=wtp.addr)


def launch(tenant_id):
    """ Initialize the module. """

    return WTPBinCounterPoller(tenant_id=tenant_id)
