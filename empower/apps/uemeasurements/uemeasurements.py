#!/usr/bin/env python3
#
# Copyright (c) 2020 Roberto Riggio
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

"""UE measurements module."""

import enum

from construct import Struct, Int16ub, Container

import empower.managers.ranmanager.vbsp as vbsp

from empower.apps.uemeasurements import RRCReportAmount, RRCReportInterval
from empower.managers.ranmanager.vbsp.lteapp import ELTEApp
from empower.core.app import EVERY

PT_UE_MEASUREMENTS_SERVICE = 0x03

TLV_MEASUREMENTS_SERVICE_CONFIG = 0x08
TLV_MEASUREMENTS_SERVICE_REPORT = 0x09

UE_MEASUREMENTS_SERVICE_CONFIG = Struct(
    "rnti" / Int16ub,
    "report_interval" / Int16ub,
    "report_amount" / Int16ub,
)
UE_MEASUREMENTS_SERVICE_CONFIG.name = "ue_measurements_service_request"

UE_MEASUREMENTS_RECONF_COMPLETE = Struct(
    "meas_id" / Int16ub,
)
UE_MEASUREMENTS_RECONF_COMPLETE.name = "ue_measurements_reconf_complete"

UE_MEASUREMENTS_SERVICE_REPORT = Struct(
    "meas_id" / Int16ub,
    "pci" / Int16ub,
    "rsrp" / Int16ub,
    "rsrq" / Int16ub,
)
UE_MEASUREMENTS_SERVICE_REPORT.name = "ue_measurements_service_report"


class UEMeasurements(ELTEApp):
    """UE Measurements Primitive.

    Perform UE Measurements for the current cell (Serving Cell).

    Parameters:
        imsi: the UE IMSI (mandatory)
        every: the loop period in ms (optional, default 2000ms)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.uemeasurements.uemeasurements",
            "params": {
                "imsi": "429011234567890",
                "every": 2000
            }
        }
    """

    def __init__(self, context, service_id, imsi, interval, amount, every):

        super().__init__(context=context,
                         service_id=service_id,
                         imsi=imsi,
                         interval=interval,
                         amount=amount,
                         every=every)

        # Register messages
        parser = (vbsp.PACKET, "ue_measurements_service")
        vbsp.register_message(PT_UE_MEASUREMENTS_SERVICE, parser)

        # Data structures
        self.meas_id = None
        self.pci = None
        self.rsrp = None
        self.rsrq = None

        # Last seen time
        self.last = None

    def __eq__(self, other):
        return super().__eq__(other) and self.imsi == other.imsi and \
            self.interval == other.interval and self.amount == other.amount

    def start(self):
        """Start app."""

        super().start()

        if self.imsi not in self.context.users:
            return

        user = self.context.users[self.imsi]
        self.config_ue_measurement(user, vbsp.OP_CREATE)

    def stop(self):
        """Stop app."""

        if self.imsi not in self.context.users:
            return

        user = self.context.users[self.imsi]
        self.config_ue_measurement(user, vbsp.OP_DELETE)

        super().stop()

    @property
    def imsi(self):
        """ Return the UE IMSI. """

        return self.params['imsi']

    @imsi.setter
    def imsi(self, imsi):
        """ Set the UE IMSI. """

        self.params['imsi'] = int(imsi)

    @property
    def interval(self):
        """ Return the interval. """

        return self.params['interval'].name

    @interval.setter
    def interval(self, interval):
        """Set the interval. """

        self.params['interval'] = RRCReportInterval[interval].name

    @property
    def amount(self):
        """ Return the amount. """

        return self.params['amount'].name

    @amount.setter
    def amount(self, amount):
        """ Set the amount. """

        self.params['amount'] = RRCReportAmount[amount].name

    def loop(self):
        """Periodic loop."""

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['meas_id'] = self.meas_id
        out['pci'] = self.pci
        out['rsrp'] = self.rsrp
        out['rsrq'] = self.rsrq

        return out

    def config_ue_measurement(self, user, crud):
        """Send UE measurement config."""

        report_interval = RRCReportInterval[self.interval].value
        report_amount = RRCReportAmount[self.amount].value

        rrc_measurement_tlv = \
            Container(rnti=user.rnti,
                      report_interval=report_interval,
                      report_amount=report_amount)

        value = UE_MEASUREMENTS_SERVICE_CONFIG.build(rrc_measurement_tlv)

        tlv = Container()
        tlv.type = TLV_MEASUREMENTS_SERVICE_CONFIG
        tlv.length = 4 + len(value)
        tlv.value = value

        tlvs.append(tlv)

        user.vbs.connection.send_message(action=PT_UE_MEASUREMENTS_SERVICE,
                                         msg_type=vbsp.MSG_TYPE_REQUEST,
                                         crud_result=crud,
                                         tlvs=tlvs,
                                         callback=self.handle_response)

    def handle_ue_join(self, user):
        """Called when a UE joins the network."""

        self.config_ue_measurement(user, vbsp.OP_CREATE)

    def handle_ue_leave(self, user):
        """Called when a UE leaves the network."""

        self.config_ue_measurement(user, vbsp.OP_DELETE)

    def handle_response(self, *args, **kwargs):
        """Handle an incoming UE_MEASUREMENTS message."""

        print(args)
        print(kwargs)


def launch(context, service_id, imsi, interval, amount, every=EVERY):
    """ Initialize the module. """

    return UEMeasurements(context=context, service_id=service_id,
                          imsi=imsi, interval=interval, amount=amount,
                          every=EVERY)
