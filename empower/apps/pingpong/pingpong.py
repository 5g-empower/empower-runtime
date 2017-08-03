#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""Ping-pong handover App."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.datatypes.etheraddress import EtherAddress

DEFAULT_LVAP = "18:5E:0F:E3:B8:68"
DEFAULT_WTPS = "00:0D:B9:2F:56:58,00:0D:B9:2F:56:5C,00:0D:B9:2F:56:64"


class PingPong(EmpowerApp):
    """Ping-pong handover App.

    Command Line Parameters:

        tenant_id: tenant id
        lvap: the lvap address (optinal, default 00:18:DE:CC:D3:40)
        wtps: comma separated list (optional, default 00:0D:B9:2F:56:58,
            00:0D:B9:2F:56:5C, 00:0D:B9:2F:56:64)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.pingpong.pingpong \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        self.__lvap_addr = None
        self.__wtp_addrs = []
        EmpowerApp.__init__(self, **kwargs)
        self.idx = 0

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
        self.log.info("LVAP %s moving to WTP %s" % (lvap.addr, wtp.addr))
        lvap.wtp = wtp


def launch(tenant_id, lvap=DEFAULT_LVAP, wtps=DEFAULT_WTPS,
           period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return PingPong(tenant_id=tenant_id, lvap_addr=lvap, wtp_addrs=wtps,
                    every=period)
