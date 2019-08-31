#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""Tutorial: Primitives."""

import uuid

from empower.core.app import EApp
from empower.core.app import EVERY

from empower.primitives.lvapbincounter.lvapbincounter import LVAPBinCounter


class HelloWorld(EApp):
    """Tutorial: Primitives.

    This app shows how to use the LVAPBinCounter primitive inside another app.

    Parameters:
        service_id: the service id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)
        every: the loop period in ms (optional, default 2000ms)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.helloworld.helloworld",
            "params": {
                "every": 2000
            }
        }
    """

    def __init__(self, service_id, project_id, every=EVERY):

        super().__init__(service_id=service_id,
                         project_id=project_id,
                         every=every)

        self.cnts = {}

    def counter_callback(self, counters):
        """Called when a new measurement is available."""

        import pprint

        pprint.pprint(counters)
        accum = []

        accum.append("sta %s " % counters['sta'])
        accum.append("tx_packets %s " % counters['tx_packets'])
        accum.append("rx_packets %s " % counters['rx_packets'])
        accum.append("rx_bytes %s " % counters['rx_bytes'])
        accum.append("tx_packets %s " % counters['tx_packets'])
        accum.append("tx_packets %s " % counters['tx_packets'])

        self.log.info("New counters: %s", "".join(accum))

    def lvap_join(self, lvap):
        """Called when an LVAP joins."""

        self.cnts[lvap.addr] = \
            LVAPBinCounter(service_id=uuid.uuid4(), project_id=self.project_id,
                           sta=lvap.addr, every=self.every)

        self.cnts[lvap.addr].start(False)

        self.cnts[lvap.addr].add_callback("counters", self.counter_callback)

    def lvap_leave(self, lvap):
        """Called when an LVAP joins."""

        if lvap.addr not in self.cnts:
            return

        self.cnts[lvap.addr].stop(False)
        del self.cnts[lvap.addr]

    def stop(self, save):
        """Stop app."""

        for cnt in self.cnts:
            self.cnts[cnt].stop(False)

        super().stop(save)


def launch(service_id, project_id, every=EVERY):
    """ Initialize the module. """

    return HelloWorld(service_id=service_id,
                      project_id=project_id,
                      every=every)
