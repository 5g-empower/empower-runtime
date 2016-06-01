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


class EventsApp(EmpowerApp):
    """Events App.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.events.events:$ID

    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.vbspup(callback=self.vbsp_up_callback)
        self.vbspdown(callback=self.vbsp_down_callback)
        self.cppup(callback=self.cpp_up_callback)
        self.cppdown(callback=self.cpp_down_callback)
        self.wtpup(callback=self.wtp_up_callback)
        self.wtpdown(callback=self.wtp_down_callback)
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)
        self.lvnfjoin(callback=self.lvnf_join_callback)
        self.lvnfleave(callback=self.lvnf_leave_callback)

    def vbsp_down_callback(self, vbsp):
        """Called when an VBSP disconnects from a tennant."""

        self.log.info("VBSP %s disconnected" % vbsp.addr)

    def vbsp_up_callback(self, vbsp):
        """Called when an VBSP connects to a tennant."""

        self.log.info("VBSP %s connected" % vbsp.addr)

    def lvnf_join_callback(self, lvnf):
        """Called when an LVNF associates to a tennant."""

        self.log.info("LVNF %s joined %s" % (lvnf.lvnf_id, lvnf.tenant_id))

    def lvnf_leave_callback(self, lvnf):
        """Called when an LVNF associates to a tennant."""

        self.log.info("LVNF %s left %s" % (lvnf.lvnf_id, lvnf.tenant_id))

    def lvap_leave_callback(self, lvap):
        """Called when an LVAP disassociates from a tennant."""

        self.log.info("LVAP %s left %s" % (lvap.addr, lvap.ssid))

    def lvap_join_callback(self, lvap):
        """Called when an LVAP associates to a tennant."""

        self.log.info("LVAP %s joined %s" % (lvap.addr, lvap.ssid))

    def wtp_up_callback(self, wtp):
        """Called when a new wtp connects to the controller."""

        self.log.info("WTP %s connected!" % wtp.addr)

    def wtp_down_callback(self, wtp):
        """Called when a wtp connectdiss from the controller."""

        self.log.info("WTP %s left!" % wtp.addr)

    def cpp_up_callback(self, cpp):
        """Called when a new cpp connects to the controller."""

        self.log.info("CPP %s connected!" % cpp.addr)

    def cpp_down_callback(self, cpp):
        """Called when a cpp disconnects from the controller."""

        self.log.info("CPP %s left!" % cpp.addr)


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return EventsApp(tenant_id=tenant_id, every=every)
