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

"""Summary triggers module."""

from construct import Container
from construct import Struct
from construct import SBInt8
from construct import UBInt8
from construct import UBInt16
from construct import SBInt16
from construct import UBInt32
from construct import UBInt64
from construct import Bytes
from construct import Sequence
from construct import Array

from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import bind_module
from empower.core.restserver import RESTServer
from empower.charybdis.lvapp.lvappserver import LVAPPServer
from empower.charybdis.triggers.triggers import TriggerWorker
from empower.charybdis.triggers.triggers import Trigger
from empower.core.module import ModuleHandler
from empower.charybdis.lvapp import PT_VERSION
from empower.charybdis.lvapp import PT_HELLO
from empower.charybdis.lvapp import PT_BYE
from empower.charybdis.lvapp import PT_LVAP_JOIN
from empower.charybdis.lvapp import PT_LVAP_LEAVE

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()

PT_ADD_SUMMARY = 0x22
PT_SUMMARY = 0x23
PT_DEL_SUMMARY = 0x24

ADD_SUMMARY = Struct("add_summary", UBInt8("version"),
                     UBInt8("type"),
                     UBInt16("length"),
                     UBInt32("seq"),
                     UBInt32("trigger_id"),
                     SBInt16("limit"),
                     UBInt16("every"),
                     Bytes("sta", 6))

SUMMARY_ENTRY = Sequence("frames",
                         Bytes("addr", 6),
                         UBInt64("tsft"),
                         UBInt16("seq"),
                         SBInt8("rssi"),
                         UBInt8("rate"),
                         UBInt8("type"),
                         UBInt8("subtype"),
                         UBInt32("length"),
                         UBInt32("dur"))

SUMMARY_TRIGGER = Struct("summary", UBInt8("version"),
                         UBInt8("type"),
                         UBInt16("length"),
                         UBInt32("seq"),
                         UBInt32("trigger_id"),
                         Bytes("wtp", 6),
                         Bytes("sta", 6),
                         UBInt16("nb_entries"),
                         Array(lambda ctx: ctx.nb_entries, SUMMARY_ENTRY))

DEL_SUMMARY = Struct("del_summary", UBInt8("version"),
                     UBInt8("type"),
                     UBInt16("length"),
                     UBInt32("seq"),
                     UBInt32("trigger_id"),
                     Bytes("sta", 6))


class Summary(Trigger):

    """ Summary object. """

    # parametes
    _keep = 0
    _limit = -1
    _rates = [12, 18, 24, 36, 48, 72, 96, 108]

    # data structures
    frames = {}
    drifts = {}
    ref = None
    first_tsft = None

    @property
    def rates(self):
        return self._rates

    @rates.setter
    def rates(self, value):
        self._rates = value

    @property
    def keep(self):
        return self._keep

    @keep.setter
    def keep(self, value):
        if value < 0:
            raise ValueError("Invalid keep value (%u)" % value)
        self._keep = value

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, value):
        if value < -1:
            raise ValueError("Invalid limit value (%u)" % value)
        self._limit = value

    def handle_trigger(self, message):
        """ Handle trigger. """

        LOG.info("Summary trigger from %s @ %s (id=%u, frames=%u)",
                 EtherAddress(message.sta),
                 EtherAddress(message.wtp),
                 message.trigger_id,
                 len(message.frames))

        sta_addr = EtherAddress(message.sta)

        if sta_addr not in self.frames:
            self.frames[sta_addr] = {}

        wtp_addr = EtherAddress(message.wtp)

        if wtp_addr not in self.frames[sta_addr]:
            self.frames[sta_addr][wtp_addr] = []

        if wtp_addr not in self.drifts:
            self.drifts[wtp_addr] = None

        if len(self.frames[sta_addr][wtp_addr]) > self.keep:
            self.frames[sta_addr][wtp_addr] = []

        for recv in message.frames:

            frame = {'tsft': recv[1],
                     'seq': recv[2],
                     'rssi': recv[3],
                     'rate': recv[4],
                     'type': recv[5],
                     'subtype': recv[6],
                     'length': recv[7],
                     'dur': recv[8]}

            if frame['rate'] not in self.rates:
                continue

            if not self.ref:
                LOG.info("Setting reference wtp to %s", wtp_addr)
                self.ref = wtp_addr
                self.first_tsft = frame['tsft']

            if wtp_addr == self.ref:

                adjusted_tsft = frame['tsft']

            else:

                # begin update drifts
                found = None

                for i, j in enumerate(self.frames[sta_addr][self.ref]):
                    if j['seq'] == frame['seq']:
                        found = i

                if found:
                    ref_tsft = self.frames[sta_addr][self.ref][found]['tsft']
                    self.drifts[wtp_addr] = ref_tsft - frame['tsft']
                # end updated drifts

                if not self.drifts[wtp_addr]:
                    continue

                adjusted_tsft = frame['tsft'] + self.drifts[wtp_addr]

            frame['tsft_adj'] = adjusted_tsft
            self.frames[sta_addr][wtp_addr].append(frame)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Summary """

        out = super().to_dict()

        out['keep'] = self.keep
        out['limit'] = self.ref
        out['rates'] = self.rates
        out['ref'] = self.ref
        out['drifts'] = {str(j): w for j, w in self.drifts.items()}

        return out


class SummaryHandler(ModuleHandler):
    pass


class SummaryWorker(TriggerWorker):
    """ Trigger worker. """

    MODULE_NAME = "summary"
    MODULE_HANDLER = SummaryHandler
    MODULE_TYPE = Summary

    TRIGGER_MSG_TYPE = PT_SUMMARY
    TRIGGER_MSG = SUMMARY_TRIGGER

    sent = {}

    def add_trigger(self, wtp, lvap, trigger):
        """ Send an add trigger message. """

        add_trigger = Container(version=PT_VERSION,
                                type=PT_ADD_SUMMARY,
                                length=22,
                                seq=wtp.seq,
                                trigger_id=trigger.module_id,
                                limit=trigger.limit,
                                every=trigger.every,
                                sta=lvap.addr.to_raw())

        LOG.info("Adding summary for sta %s @ %s (id=%u)",
                 lvap.addr,
                 wtp.addr,
                 trigger.module_id)

        msg = ADD_SUMMARY.build(add_trigger)
        wtp.connection.stream.write(msg)

    def del_trigger(self, wtp, lvap, trigger):
        """ Send an del trigger message. """

        del_trigger = Container(version=PT_VERSION,
                                type=PT_DEL_SUMMARY,
                                length=22,
                                seq=wtp.get_next_seq(),
                                trigger_id=trigger.module_id,
                                limit=trigger.limit,
                                every=trigger.every,
                                sta=lvap.addr.to_raw())

        LOG.info("Deleting summary for sta %s @ %s (id=%u)",
                 lvap.addr,
                 wtp.addr,
                 trigger.module_id)

        msg = DEL_SUMMARY.build(del_trigger)
        wtp.connection.stream.write(msg)


bind_module(SummaryWorker)


def launch():
    """ Initialize the module. """

    lvap_server = RUNTIME.components[LVAPPServer.__module__]
    rest_server = RUNTIME.components[RESTServer.__module__]

    worker = SummaryWorker(rest_server)

    lvap_server.register_message(PT_HELLO, None, worker.handle_hello)
    lvap_server.register_message(PT_LVAP_JOIN, None, worker.handle_lvap_join)
    lvap_server.register_message(PT_LVAP_LEAVE, None, worker.handle_lvap_leave)
    lvap_server.register_message(PT_BYE, None, worker.handle_bye)
    lvap_server.register_message(PT_SUMMARY,
                                 SUMMARY_TRIGGER,
                                 worker.handle_trigger)

    return worker
