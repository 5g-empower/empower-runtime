#!/usr/bin/env python3
#
# Copyright (c) 2021 Roberto Riggio
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

"""Bitrate predictor app."""

import time

from empower_core.app import EVERY

from empower.managers.ranmanager.vbsp.lteapp import ELTEApp
from empower.apps.uemeasurements import RRCReportAmount, RRCReportInterval


class Predictor(ELTEApp):
    """Bitrate predictor app.

    Predicts bitrate starting from RSRP/RSRQ measurements

    Parameters:
        imsi: the UE IMSI (mandatory)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.predictor.predictor",
            "params": {
                "imsi": "429011234567890"
            }
        }
    """

    def __init__(self, context, service_id, imsi, every):

        super().__init__(context=context,
                         service_id=service_id,
                         imsi=imsi,
                         every=every)

        # Data structures
        self.measurements = []

        # UE Measurement App
        self.ue_meas = None

        # Last seen time
        self.last = None

    def __eq__(self, other):
        return super().__eq__(other) and self.imsi == other.imsi

    def start(self):
        """Start app."""

        super().start()

        self.ue_meas = \
            self.register_service("empower.apps.uemeasurements.uemeasurements",
                                  imsi=self.imsi.to_str(),
                                  meas_id=1,
                                  interval=RRCReportInterval.MS240.name,
                                  amount=RRCReportAmount.INFINITY.name)

        self.ue_meas.add_callback(callback=self.process_measurements)

    def stop(self):
        """Stop app."""

        self.unregister_service(self.ue_meas.service_id)

        super().stop()

    def process_measurements(self, meas):
        """Process new measurements."""

        arrival = time.time()

        self.log.info("Time %u, RSRP %d, RSRQ %d", time.time(), meas.rsrp,
                      meas.rsrq)

        self.measurements.append([arrival, meas.rsrp, meas.rsrq])

    @property
    def imsi(self):
        """ Return the UE IMSI. """

        return self.params['imsi']

    @imsi.setter
    def imsi(self, imsi):
        """ Set the UE IMSI. """

        self.params['imsi'] = self.validate_param('imsi', imsi)

    def loop(self):
        """Periodic loop."""

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()
        out['measurements'] = self.measurements
        return out


def launch(context, service_id, imsi, every=EVERY):
    """ Initialize the module. """

    return Predictor(context=context, service_id=service_id, imsi=imsi,
                     every=every)
