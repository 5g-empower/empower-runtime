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

"""Tenant scheduler."""

from empower.core.app import EmpowerBaseApp
from empower.wtp_bin_counter import send_stats_request
from empower.wtp_bin_counter import parse_stats_response
from empower.wtp_bin_counter import register_callback
from empower.wtp_bin_counter import get_module_id

from empower.main import RUNTIME

DEFAULT_PERIOD = 5000


class TenantScheduler(EmpowerBaseApp):
    """Tenant Scheduler."""

    def __init__(self, **kwargs):
        EmpowerBaseApp.__init__(self, **kwargs)

        self.wtps = {}
        self.module_id = get_module_id()

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Stats """

        out = super().to_dict()

        out['wtps'] = {}

        for addr in self.wtps:
            out['wtps'][str(addr)] = \
                {str(k): v for k, v in self.wtps[addr].items()}

        return out

    def loop(self):
        """Periodic job."""

        for tenant in RUNTIME.tenants.values():
            for wtp in tenant.wtps.values():
                send_stats_request(wtp, self.module_id)

    def fill_samples(self, parsed, field):

        wtp_addr = parsed['wtp']

        if wtp_addr not in self.wtps:
            self.wtps[wtp_addr] = {}

        for lvap_addr in parsed[field]:

            lvap = RUNTIME.lvaps[lvap_addr]

            if not lvap.tenant:
                continue

            tenant_id = lvap.tenant.tenant_id

            if tenant_id not in self.wtps[wtp_addr]:
                self.wtps[wtp_addr][tenant_id] = {}

            if field not in self.wtps[wtp_addr][tenant_id]:
                self.wtps[wtp_addr][tenant_id][field] = 0

            self.wtps[wtp_addr][tenant_id][field] += \
                parsed[field][lvap_addr][0]

    def handle_stats(self, stats):
        """Handle wtp bin counter response."""

        parsed = parse_stats_response(stats)

        if parsed['module_id'] != self.module_id:
            return

        self.fill_samples(parsed, 'tx_bytes')
        self.fill_samples(parsed, 'rx_bytes')
        self.fill_samples(parsed, 'tx_packets')
        self.fill_samples(parsed, 'rx_packets')


def launch(every=DEFAULT_PERIOD):
    """Start the Energino Server Module."""

    sched = TenantScheduler(every=every)
    register_callback(sched.handle_stats)
    return sched
