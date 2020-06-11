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

import time

from construct import Struct, Int16ub, Int8ub, Container

import empower.managers.ranmanager.vbsp as vbsp

from empower.apps.uemeasurements import RRCReportAmount, RRCReportInterval
from empower.managers.ranmanager.vbsp.lteapp import ELTEApp
from empower.managers.ranmanager.vbsp import MSG_TYPE_RESPONSE, RESULT_FAIL

PT_UE_MEASUREMENTS_SERVICE = 0x03

TLV_MEASUREMENTS_SERVICE_CONFIG = 0x08
TLV_MEASUREMENTS_SERVICE_REPORT = 0x09
TLV_MEASUREMENTS_SERVICE_MEAS_ID = 0x0B

UE_MEASUREMENTS_SERVICE_CONFIG = Struct(
    "rnti" / Int16ub,
    "meas_id" / Int8ub,
    "interval" / Int8ub,
    "amount" / Int8ub,
)
UE_MEASUREMENTS_SERVICE_CONFIG.name = "ue_measurements_service_request"

UE_MEASUREMENTS_SERVICE_MEAS_ID = Struct(
    "rnti" / Int16ub,
    "meas_id" / Int8ub,
)
UE_MEASUREMENTS_SERVICE_MEAS_ID.name = "ue_measurements_service_meas_id"

UE_MEASUREMENTS_SERVICE_REPORT = Struct(
    "rnti" / Int16ub,
    "meas_id" / Int8ub,
    "rsrp" / Int8ub,
    "rsrq" / Int8ub,
)
UE_MEASUREMENTS_SERVICE_REPORT.name = "ue_measurements_service_report"


class UEMeasurements(ELTEApp):
    """UE Measurements Primitive.

    Perform UE Measurements for the current cell (Serving Cell).

    Parameters:
        imsi: the UE IMSI (mandatory)
        interval: the reporting interval (mandatory)
        amount: the number of reports (mandatory)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.uemeasurements.uemeasurements",
            "params": {
                "imsi": "429011234567890",
                "interval": "MS480",
                "amount": "INFINITY"
            }
        }
    """

    def __init__(self, context, service_id, meas_id, imsi, interval, amount,
                 every):

        super().__init__(context=context,
                         service_id=service_id,
                         meas_id=meas_id,
                         imsi=imsi,
                         interval=interval,
                         amount=amount,
                         every=every)

        # Register messages
        parser = (vbsp.PACKET, "ue_measurements_service")
        vbsp.register_message(PT_UE_MEASUREMENTS_SERVICE, parser)

        # Data structures
        self.rsrp = None
        self.rsrq = None

        # Last seen time
        self.last = None

    def __eq__(self, other):
        return super().__eq__(other) and self.meas_id == other.meas_id \
            and self.imsi == other.imsi and self.interval == other.interval \
            and self.amount == other.amount

    def start(self):
        """Start app."""

        vbsp.register_callback(PT_UE_MEASUREMENTS_SERVICE,
                               self.handle_response)

        super().start()

        if self.imsi in self.context.users:
            user = self.context.users[self.imsi]
            self.handle_ue_join(user)

    def stop(self):
        """Stop app."""

        if self.imsi in self.context.users:
            user = self.context.users[self.imsi]
            self.handle_ue_leave(user)

        super().stop()

        vbsp.unregister_callback(PT_UE_MEASUREMENTS_SERVICE,
                                 self.handle_response)

    @property
    def meas_id(self):
        """ Return the meas id. """

        return self.params['meas_id']

    @meas_id.setter
    def meas_id(self, value):
        """Set the meas id. """

        self.params['meas_id'] = self.validate_param('meas_id', int(value))

    @property
    def imsi(self):
        """ Return the UE IMSI. """

        return self.params['imsi']

    @imsi.setter
    def imsi(self, imsi):
        """ Set the UE IMSI. """

        self.params['imsi'] = self.validate_param('imsi', imsi)

    @property
    def interval(self):
        """ Return the interval. """

        return self.params['interval']

    @interval.setter
    def interval(self, value):
        """Set the interval. """

        self.params['interval'] = \
            self.validate_param('interval', value)

    @property
    def amount(self):
        """ Return the amount. """

        return self.params['amount']

    @amount.setter
    def amount(self, value):
        """ Set the amount. """

        self.params['amount'] = \
            self.validate_param('amount', value)

    def loop(self):
        """Periodic loop."""

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['rsrp'] = self.rsrp
        out['rsrq'] = self.rsrq

        return out

    def handle_ue_join(self, user):
        """Called when a UE joins the network."""

        interval = RRCReportInterval[self.interval].value
        amount = RRCReportAmount[self.amount].value

        rrc_measurement_tlv = \
            Container(rnti=user.rnti,
                      meas_id=self.meas_id,
                      interval=interval,
                      amount=amount)

        value = UE_MEASUREMENTS_SERVICE_CONFIG.build(rrc_measurement_tlv)

        tlv = Container()
        tlv.type = TLV_MEASUREMENTS_SERVICE_CONFIG
        tlv.length = 4 + len(value)
        tlv.value = value

        user.vbs.connection.send_message(action=PT_UE_MEASUREMENTS_SERVICE,
                                         msg_type=vbsp.MSG_TYPE_REQUEST,
                                         crud_result=vbsp.OP_CREATE,
                                         tlvs=[tlv],
                                         callback=self.handle_add_response)

    def handle_ue_leave(self, user):
        """Called when a UE leaves the network."""

        rrc_measurement_tlv = \
            Container(rnti=user.rnti, meas_id=self.meas_id)

        value = UE_MEASUREMENTS_SERVICE_MEAS_ID.build(rrc_measurement_tlv)

        tlv = Container()
        tlv.type = TLV_MEASUREMENTS_SERVICE_MEAS_ID
        tlv.length = 4 + len(value)
        tlv.value = value

        user.vbs.connection.send_message(action=PT_UE_MEASUREMENTS_SERVICE,
                                         msg_type=vbsp.MSG_TYPE_REQUEST,
                                         crud_result=vbsp.OP_DELETE,
                                         tlvs=[tlv],
                                         callback=self.handle_del_response)

    def handle_add_response(self, msg, vbs, _):
        """Handle an incoming UE_MEASUREMENTS_SERVICE message."""

        # if not a response then ignore
        if msg.flags.msg_type != MSG_TYPE_RESPONSE:
            self.log.warning("Not a response, ignoring.")
            return

        # there should be only one tlv
        for tlv in msg.tlvs:

            if tlv.type == TLV_MEASUREMENTS_SERVICE_MEAS_ID:

                parser = UE_MEASUREMENTS_SERVICE_MEAS_ID
                option = parser.parse(tlv.value)

                # if result is fail then ignore
                if msg.tsrc.crud_result == RESULT_FAIL:
                    msg = "Error creating UE meas: %u" % option.meas_id
                else:
                    msg = "Success creating UE meas: %u" % option.meas_id

                self.log.warning(msg)

    def handle_del_response(self, msg, vbs, _):
        """Handle an incoming UE_MEASUREMENTS_SERVICE message."""

        # if not a response then ignore
        if msg.flags.msg_type != MSG_TYPE_RESPONSE:
            self.log.warning("Not a response, ignoring.")
            return

        # there should be only one tlv
        for tlv in msg.tlvs:

            if tlv.type == TLV_MEASUREMENTS_SERVICE_MEAS_ID:

                parser = UE_MEASUREMENTS_SERVICE_MEAS_ID
                option = parser.parse(tlv.value)

                # if result is fail then ignore
                if msg.tsrc.crud_result == RESULT_FAIL:
                    msg = "Error removing UE meas: %u" % option.meas_id
                else:
                    msg = "Success removing UE meas: %u" % option.meas_id

                self.log.warning(msg)

    def handle_response(self, msg, _):
        """Handle an incoming UE_MEASUREMENTS_SERVICE message."""

        # if not a response then ignore
        if msg.flags.msg_type != MSG_TYPE_RESPONSE:
            self.log.warning("Not a response, ignoring.")
            return

        # if result is fail then ignore
        if msg.tsrc.crud_result == RESULT_FAIL:
            self.log.warning("Error creating UE measurement, ignoring.")
            return

        # must be a success, parse TLVs
        for tlv in msg.tlvs:

            if tlv.type != TLV_MEASUREMENTS_SERVICE_REPORT:
                continue

            # set last iteration time
            self.last = time.time()

            parser = UE_MEASUREMENTS_SERVICE_REPORT
            option = parser.parse(tlv.value)

            self.log.debug("Processing options %s", parser.name)

            user = self.context.users[self.imsi]

            if option.rnti != user.rnti:
                continue

            if option.meas_id != self.meas_id:
                continue

            self.rsrp = option.rsrp
            self.rsrq = option.rsrq

            user.ue_measurements = {
                "rsrp": self.rsrp,
                "rsrq": self.rsrq,
            }

        # handle callbacks
        self.handle_callbacks()


def launch(context, service_id, meas_id, imsi, interval, amount, every=-1):
    """ Initialize the module. """

    return UEMeasurements(context=context, service_id=service_id,
                          meas_id=meas_id, imsi=imsi, interval=interval,
                          amount=amount, every=every)
