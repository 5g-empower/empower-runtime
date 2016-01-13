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

""" EmPOWER trigger class. """

from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import ModuleWorker
from empower.core.module import Module
from empower.core.module import handle_callback

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class Trigger(Module):
    """ Trigger object. """

    # parameters
    _lvaps = EtherAddress('FF:FF:FF:FF:FF:FF')

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Trigger """

        repr = super().to_dict()
        repr['lvaps'] = self.lvaps
        return repr

    @property
    def lvaps(self):
        """ Return the LVAPs address. """
        return self._lvaps

    @lvaps.setter
    def lvaps(self, lvaps):
        """ Set the LVAPs address. """
        self._lvaps = EtherAddress(lvaps)

    def handle_trigger(self, message):
        """ Handle trigger. """

        pass

    def __str__(self):
        return "Trigger %u lvaps %s" % (self.module_id, self.lvaps)

    def __eq__(self, other):

        return super().__eq__(other) and \
               self.lvaps == other.lvaps


class TriggerWorker(ModuleWorker):
    """ Trigger worker. """

    TRIGGER_MSG_TYPE = None
    TRIGGER_MSG = None

    sent = {}

    def handle_bye(self, wtp):
        """ Remove sent triggers history on WTP disconnect. """

        if wtp.addr in self.sent:
            LOG.info("Removing %s sent triggers", wtp.addr)
            del self.sent[wtp.addr]

    def handle_hello(self, hello):
        """ Callback on PT_HELLO message. """

        for trigger in self.modules.values():
            for lvap in RUNTIME.lvaps.values():
                self.handle_lvap_join(lvap)

    def handle_lvap_join(self, lvap):
        """ Callback on LVAP_JOIN message. """

        for trigger in self.modules.values():

            tenant = RUNTIME.tenants[trigger.tenant_id]

            if lvap.addr not in tenant.lvaps:
                continue

            if not lvap.addr.match(trigger.lvaps):
                continue

            for wtp in tenant.wtps.values():

                if not wtp.connection:
                    continue

                if wtp.addr not in self.sent:
                    self.sent[wtp.addr] = []

                if trigger in self.sent[wtp.addr]:
                    continue

                self.add_trigger(wtp, lvap, trigger)
                self.sent[wtp.addr].append(trigger)

    def handle_lvap_leave(self, lvap):
        """ Callback on LVAP_LEAVE message. """

        for trigger in self.modules.values():

            lvaps = RUNTIME.tenants[trigger.tenant_id].lvaps
            wtps = RUNTIME.tenants[trigger.tenant_id].wtps

            if lvap.addr not in lvaps:
                return

            if not lvap.addr.match(trigger.lvaps):
                continue

            for wtp in wtps.values():

                if not wtp.connection:
                    continue

                self.del_trigger(wtp, lvap, trigger)
                self.sent[wtp.addr].remove(trigger)

    def handle_trigger(self, message):
        """ Handle an incoming poller response message.
        Args:
            message, a poller response message
        Returns:
            None
        """

        if message.trigger_id not in self.modules:
            return

        wtp_addr = EtherAddress(message.wtp)

        if wtp_addr not in RUNTIME.wtps:
            return

        lvap_addr = EtherAddress(message.sta)

        # find trigger object
        trigger = self.modules[message.trigger_id]

        tenant = RUNTIME.tenants[trigger.tenant_id]

        if lvap_addr not in tenant.lvaps:
            return

        # handle the message
        trigger.handle_trigger(message)

        # call callback
        handle_callback(trigger, trigger)
