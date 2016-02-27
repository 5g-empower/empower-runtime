#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""RSSI triggers module."""

from datetime import datetime

from construct import Container
from construct import Struct
from construct import SBInt8
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes

from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import bind_module
from empower.restserver.restserver import RESTServer
from empower.lvapp.lvappserver import LVAPPServer
from empower.triggers.triggers import TriggerWorker
from empower.triggers.triggers import Trigger
from empower.core.module import ModuleHandler
from empower.lvapp import PT_VERSION
from empower.lvapp import PT_HELLO
from empower.lvapp import PT_BYE
from empower.lvapp import PT_LVAP_JOIN
from empower.lvapp import PT_LVAP_LEAVE

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

R_GT = 'GT'
R_LT = 'LT'
R_EQ = 'EQ'
R_GE = 'GE'
R_LE = 'LE'

RELATIONS = {R_EQ: 0, R_GT: 1, R_LT: 2, R_GE: 3, R_LE: 4}

PT_ADD_RSSI = 0x19
PT_RSSI = 0x20
PT_DEL_RSSI = 0x21

ADD_RSSI_TRIGGER = Struct("add_rssi_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt16("length"),
                          UBInt32("seq"),
                          UBInt32("trigger_id"),
                          Bytes("sta", 6),
                          UBInt8("relation"),
                          SBInt8("value"))

RSSI_TRIGGER = Struct("rssi_trigger", UBInt8("version"),
                      UBInt8("type"),
                      UBInt16("length"),
                      UBInt32("seq"),
                      UBInt32("trigger_id"),
                      Bytes("wtp", 6),
                      Bytes("sta", 6),
                      UBInt8("relation"),
                      SBInt8("value"),
                      SBInt8("current"))


DEL_RSSI_TRIGGER = Struct("del_rssi_trigger", UBInt8("version"),
                          UBInt8("type"),
                          UBInt16("length"),
                          UBInt32("seq"),
                          UBInt32("trigger_id"),
                          Bytes("sta", 6),
                          UBInt8("relation"),
                          SBInt8("value"))


class RSSI(Trigger):

    """ RSSI trigger object. """

    # parameters
    _relation = 'GT'
    _value = -90

    # data strctures
    events = []

    def handle_trigger(self, message):
        """ Handle an incoming RSSI_TRIGGER message.
        Args:
            message, a RSSI_TRIGGER message
        Returns:
            None
        """

        if message.relation == RELATIONS['EQ']:
            relation = 'EQ'
        elif message.relation == RELATIONS['GT']:
            relation = 'GT'
        elif message.relation == RELATIONS['LT']:
            relation = 'LT'
        elif message.relation == RELATIONS['GE']:
            relation = 'GE'
        elif message.relation == RELATIONS['LE']:
            relation = 'LE'

        LOG.info("RSSI trigger: %s RSSI @ %s %s %s at %s (id=%u)",
                 EtherAddress(message.sta),
                 EtherAddress(message.wtp),
                 relation,
                 message.value,
                 message.current,
                 message.trigger_id)

        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        rssi_event = {'timestamp': timestamp,
                      'lvap': EtherAddress(message.sta),
                      'wtp': EtherAddress(message.wtp),
                      'relation': relation,
                      'value': message.value,
                      'current': message.current}

        self.events.append(rssi_event)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Trigger """

        out = super().to_dict()

        out['relation'] = self.relation
        out['lvaps'] = self.lvaps
        out['value'] = self.value
        out['events'] = self.events

        return out

    @property
    def relation(self):
        """ Return the relation. """
        return self._relation

    @relation.setter
    def relation(self, relation):
        """ Set the relation. """
        if relation not in RELATIONS:
            raise ValueError("Valid relations are: %s" %
                             ','.join(RELATIONS.keys()))

        self._relation = relation

    @property
    def value(self):
        """ Return the value. """
        return self._value

    @value.setter
    def value(self, value):
        """ Set the value. """

        if value < -128 or value > 127:
            raise ValueError("rssi requires -128 <= value <= 127")

        self._value = int(value)

    def __str__(self):
        return "Trigger %u rssi @ %s %s %u" % (self.module_id,
                                               self.lvaps,
                                               self.relation,
                                               self.value)

    def __eq__(self, other):

        return super().__eq__(other) and \
               self.value == other.value


class RSSIHandler(ModuleHandler):
    pass


class RSSIWorker(TriggerWorker):
    """ Trigger worker. """

    MODULE_NAME = "rssi"
    MODULE_HANDLER = RSSIHandler
    MODULE_TYPE = RSSI

    TRIGGER_MSG_TYPE = PT_RSSI
    TRIGGER_MSG = RSSI_TRIGGER

    sent = {}

    def add_trigger(self, wtp, lvap, trigger):
        """ Send an ADD_RSSI_TRIGGER message.

        Args:
            sta: an EtherAddress object specifing the target STA
            relation: the check to be enforced (EQ, GT, LT, LE, GE)
            value: the comparison argument
        Returns:
            None
        Raises:
            TypeError: if sta is not an EtherAddress object.
        """

        add_trigger = Container(version=PT_VERSION,
                                type=PT_ADD_RSSI,
                                length=20,
                                seq=wtp.seq,
                                trigger_id=trigger.module_id,
                                sta=lvap.addr.to_raw(),
                                relation=RELATIONS[trigger.relation],
                                value=trigger.value)

        LOG.info("Adding trigger for sta %s: RSSI @ %s %s %s (id=%u)",
                 lvap.addr,
                 wtp.addr,
                 trigger.relation,
                 trigger.value,
                 trigger.module_id)

        msg = ADD_RSSI_TRIGGER.build(add_trigger)
        wtp.connection.stream.write(msg)

    def del_trigger(self, wtp, lvap, trigger):
        """ Send an del trigger message. """

        del_trigger = Container(version=PT_VERSION,
                                type=PT_DEL_RSSI,
                                length=20,
                                seq=wtp.seq,
                                trigger_id=trigger.module_id,
                                sta=lvap.addr.to_raw(),
                                relation=RELATIONS[trigger.relation],
                                value=trigger.value)

        LOG.info("Deleting trigger for sta %s: RSSI @ %s %s %s (id=%u)",
                 lvap.addr,
                 wtp.addr,
                 trigger.relation,
                 trigger.value,
                 trigger.module_id)

        msg = DEL_RSSI_TRIGGER.build(del_trigger)
        wtp.connection.stream.write(msg)


bind_module(RSSIWorker)


def launch():
    """ Initialize the module. """

    lvap_server = RUNTIME.components[LVAPPServer.__module__]
    rest_server = RUNTIME.components[RESTServer.__module__]

    worker = RSSIWorker(rest_server)

    lvap_server.register_message(PT_HELLO, None, worker.handle_hello)
    lvap_server.register_message(PT_LVAP_JOIN, None, worker.handle_lvap_join)
    lvap_server.register_message(PT_LVAP_LEAVE, None, worker.handle_lvap_leave)
    lvap_server.register_message(PT_BYE, None, worker.handle_bye)
    lvap_server.register_message(PT_RSSI, RSSI_TRIGGER, worker.handle_trigger)

    return worker
