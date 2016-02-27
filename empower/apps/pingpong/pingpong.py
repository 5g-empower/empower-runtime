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

"""Ping-pong handover App."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.datatypes.etheraddress import EtherAddress

import empower.logger
LOG = empower.logger.get_logger()

DEFAULT_LVAP = "00:18:DE:CC:D3:40"
DEFAULT_WTPS = "00:0D:B9:2F:56:58,00:0D:B9:2F:56:5C,00:0D:B9:2F:56:64"


class PingPong(EmpowerApp):
    """Ping-pong handover App.

    Command Line Parameters:

        lvap: the lvap address (optinal, default 00:18:DE:CC:D3:40)
        wtps: comma separated list (optional)
        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.pingpong.pingpong:$ID

    """

    def __init__(self, tenant, **kwargs):

        self.__lvap_addr = None
        self.__wtp_addrs = []
        self.idx = 0

        EmpowerApp.__init__(self, tenant, **kwargs)

    @property
    def wtp_addrs(self):
        """Return wtp_addrs."""

        return self.__wtp_addrs

    @wtp_addrs.setter
    def wtp_addrs(self, value):
        """Set wtp_addrs."""

        self.__wtp_addrs = [EtherAddress(x) for x in value.split(",")]

    @property
    def lvap_addr(self):
        """Return lvap_addr."""

        return self.__lvap_addr

    @lvap_addr.setter
    def lvap_addr(self, value):
        """Set lvap_addr."""

        self.__lvap_addr = EtherAddress(value)

    def loop(self):
        """ Periodic job. """

        # if the LVAP is not active, then return
        lvap = self.lvap(self.lvap_addr)
        if not lvap:
            return

        wtp_addr = self.wtp_addrs[self.idx % len(self.wtp_addrs)]
        self.idx = self.idx + 1

        wtp = self.wtp(wtp_addr)

        if not wtp or not wtp.connection:
            return

        # perform handover
        LOG.info("LVAP %s moving to WTP %s" % (lvap.addr, wtp.addr))
        lvap.wtp = wtp


def launch(tenant, lvap=DEFAULT_LVAP,
           wtps=DEFAULT_WTPS,
           period=DEFAULT_PERIOD):

    """ Initialize the module. """

    return PingPong(tenant, lvap_addr=lvap, wtp_addrs=wtps, every=period)
