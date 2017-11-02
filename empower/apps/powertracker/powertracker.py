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

"""Application tracking pool-wide power consumption."""

import time

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class PowerTracker(EmpowerApp):
    """Application tracking pool-wide power consumption.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.powertracker.powertracker \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filename = "./powertracker.csv"

    def loop(self):
        """ Periodic job. """

        power = 0.0

        for wtp in self.wtps():
            if not wtp.feed:
                continue
            for datastream in wtp.feed.datastreams.values():
                if datastream['id'] == 'power':
                    power += datastream['current_value']

        line = "%u %f\n" % (time.time(), power)

        with open(self.filename, 'a') as file_d:
            file_d.write(line)


def launch(tenant_id, filename="./powertracker.csv", every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return PowerTracker(tenant_id=tenant_id, filename=filename, every=every)
