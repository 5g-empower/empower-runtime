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

"""Link statistics module."""

from construct import UBInt8
from construct import Bytes
from construct import Sequence
from construct import Container
from construct import Struct
from construct import UBInt16
from construct import UBInt32
from construct import Array

from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import ModuleHandler
from empower.core.module import ModuleWorker
from empower.core.module import Module
from empower.core.module import bind_module
from empower.core.module import handle_callback
from empower.core.restserver import RESTServer
from empower.lvapp.lvappserver import LVAPPServer
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


PT_RATES_REQUEST = 0x29
PT_RATES_RESPONSE = 0x30

RATES_ENTRY = Sequence("rates",
                       UBInt8("rate"),
                       UBInt8("prob"))


RATES_REQUEST = Struct("rates_request", UBInt8("version"),
                       UBInt8("type"),
                       UBInt16("length"),
                       UBInt32("seq"),
                       UBInt32("rates_id"),
                       Bytes("sta", 6))

RATES_RESPONSE = Struct("rates_response", UBInt8("version"),
                        UBInt8("type"),
                        UBInt16("length"),
                        UBInt32("seq"),
                        UBInt32("rates_id"),
                        Bytes("wtp", 6),
                        Bytes("sta", 6),
                        UBInt16("nb_entries"),
                        Array(lambda ctx: ctx.nb_entries, RATES_ENTRY))


class LinkStatsHandler(ModuleHandler):
    pass


class LinkStats(Module):
    """ PacketsCounter object. """

    REQUIRED = ['module_type', 'worker', 'tenant_id', 'lvap']

    # parameters
    _lvap = None

    # data structure
    rates = {}

    def __eq__(self, other):

        return super().__eq__(other) and \
               self.lvap == other.lvap

    @property
    def lvap(self):
        return self._lvap

    @lvap.setter
    def lvap(self, value):
        self._lvap = EtherAddress(value)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Rates """

        out = super().to_dict()

        out['lvap'] = self.lvap
        out['rates'] = {str(k): v for k, v in self.rates.items()}

        return out

    def run_once(self):
        """ Send out rate request. """

        if self.tenant_id not in RUNTIME.tenants:
            return

        lvaps = RUNTIME.tenants[self.tenant_id].lvaps

        if self.lvap not in lvaps:
            return

        lvap = lvaps[self.lvap]

        if not lvap.wtp.connection:
            return

        self.send_rates_request(lvap.wtp, lvap)

    def send_rates_request(self, wtp, lvap):
        """ Send a RATES_REQUEST message. """

        rates_req = Container(version=PT_VERSION,
                              type=PT_RATES_REQUEST,
                              length=18,
                              seq=wtp.seq,
                              rates_id=self.module_id,
                              sta=lvap.addr.to_raw())

        LOG.info("Sending rates request to %s @ %s (id=%u)",
                 lvap.addr, wtp.addr, self.module_id)

        msg = RATES_REQUEST.build(rates_req)
        wtp.connection.stream.write(msg)


class LinkStatsWorker(ModuleWorker):
    """ Counter worker. """

    MODULE_NAME = "link_stats"
    MODULE_HANDLER = LinkStatsHandler
    MODULE_TYPE = LinkStats

    def handle_rates_response(self, rates):
        """Handle an incoming RATES_RESPONSE message.
        Args:
            rates, a RATES_RESPONSE message
        Returns:
            None
        """

        if rates.rates_id not in self.modules:
            return

        counter = self.modules[rates.rates_id]

        # update cache
        lvap = RUNTIME.lvaps[counter.lvap]
        lvap.rates = {x[0]: x[1] for x in rates.rates}

        # update this object
        counter.rates = {x[0]: x[1] for x in rates.rates}

        # call callback
        if counter.callback:
            handle_callback(counter, counter)


bind_module(LinkStatsWorker)


def launch():
    """ Initialize the module. """

    lvap_server = RUNTIME.components[LVAPPServer.__module__]
    rest_server = RUNTIME.components[RESTServer.__module__]

    worker = LinkStatsWorker(rest_server)
    lvap_server.register_message(PT_RATES_RESPONSE,
                                 RATES_RESPONSE,
                                 worker.handle_rates_response)

    return worker
