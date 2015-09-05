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

"""Events Apps."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD

import empower.logger
LOG = empower.logger.get_logger()


class EventsApp(EmpowerApp):
    """Events App.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.events.events:$ID

    """

    def __init__(self, tenant_id, period):
        super().__init__(tenant_id, period)
        self.cppup(callback=self.cpp_up_callback)
        self.cppdown(callback=self.cpp_down_callback)
        self.wtpup(callback=self.wtp_up_callback)
        self.wtpdown(callback=self.wtp_down_callback)
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)

    def lvap_leave_callback(self, lvap):
        """Called when an LVAP disassociates from a tennant."""

        LOG.info("LVAP %s left %s" % (lvap.addr, lvap.ssid))

    def lvap_join_callback(self, lvap):
        """Called when an LVAP associates to a tennant."""

        LOG.info("LVAP %s joined %s" % (lvap.addr, lvap.ssid))

    def wtp_up_callback(self, wtp):
        """Called when a new wtp connects to the controller."""

        LOG.info("WTP %s connected!" % wtp.addr)

    def wtp_down_callback(self, wtp):
        """Called when a wtp connectdiss from the controller."""

        LOG.info("WTP %s left!" % wtp.addr)

    def cpp_up_callback(self, cpp):
        """Called when a new cpp connects to the controller."""

        LOG.info("CPP %s connected!" % cpp.addr)

    def cpp_down_callback(self, cpp):
        """Called when a cpp disconnects from the controller."""

        LOG.info("CPP %s left!" % cpp.addr)

    def loop(self):
        """Periodic job."""

        pass


def launch(tenant, period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return EventsApp(tenant, period)
