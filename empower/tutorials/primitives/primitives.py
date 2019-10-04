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

import pprint
import time

from empower.core.app import EApp
from empower.core.app import EVERY


class TutorialPrimitives(EApp):
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

        self.counters = {}

    @property
    def last_run(self):
        """Return last_run."""

        return self.storage["last_run"]

    @last_run.setter
    def last_run(self, value):
        """Set last_run."""

        self.storage["last_run"] = value
        self.save_service_state()

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = super().to_dict()
        output['counters'] = self.counters
        return output

    def counters_callback(self, counters):
        """Called when a new measurement is available."""

        accum = []

        accum.append("sta %s " % counters['sta'])
        accum.append("tx_packets %s " % counters['tx_packets'])
        accum.append("rx_packets %s " % counters['rx_packets'])
        accum.append("rx_bytes %s " % counters['rx_bytes'])
        accum.append("tx_packets %s " % counters['tx_packets'])
        accum.append("tx_packets %s " % counters['tx_packets'])

        self.last_run = time.time()

        self.log.info("New counters: %s", "".join(accum))

    def lvap_join(self, lvap):
        """Called when an LVAP joins."""

        name = "empower.primitives.lvapbincounter.lvapbincounter"
        app = self.get_service(name, sta=lvap.addr)
        app.add_callback("counters", self.counters_callback)

        self.counters[lvap.addr] = app


def launch(service_id, project_id, every=EVERY):
    """ Initialize the module. """

    return TutorialPrimitives(service_id=service_id,
                              project_id=project_id,
                              every=every)
