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

"""Application implementing an rssi tracker."""

from empower.datatypes.etheraddress import EtherAddress
from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.maps.ucqm import ucqm
from empower.maps.ncqm import ncqm
from empower.events.wtpup import wtpup

DEFAULT_ADDRESS = "ff:ff:ff:ff:ff:ff"


class RSSITracker(EmpowerApp):
    """Application implementing an rssi tracker.

    Command Line Parameters:

        addrs: the addresses to be tracked (optional, default f:ff:ff:ff:ff:ff)
        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.rssitracker.rssitracker:$ID

    """

    def __init__(self, tenant, **kwargs):
        self.__addrs = None
        EmpowerApp.__init__(self, tenant, **kwargs)
        wtpup(tenant_id=self.tenant.tenant_id, callback=self.wtp_up_callback)

    @property
    def addrs(self):
        """Return addrs."""

        return self.__addrs

    @addrs.setter
    def addrs(self, value):
        """Set addrs."""

        self.__addrs = EtherAddress(value)

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        for block in wtp.supports:

            ucqm(addrs=self.addrs,
                 block=block,
                 tenant_id=self.tenant.tenant_id,
                 every=self.every,
                 callback=self.ucqm_callback)

            ncqm(addrs=self.addrs,
                 block=block,
                 tenant_id=self.tenant.tenant_id,
                 every=self.every,
                 callback=self.ncqm_callback)

    def ucqm_callback(self, poller):
        """Called when a UCQM response is received from a WTP."""

        import time

        filename = "ucqm_%s_%u_%s.csv" % (poller.block.addr,
                                          poller.block.channel,
                                          poller.block.band)

        for addr in poller.maps.values():

            line = "%f,%s,%.2f,%.2f,%u,%.2f,%.2f\n" % (time.time(),
                                                       addr['addr'],
                                                       addr['last_rssi_avg'],
                                                       addr['last_rssi_std'],
                                                       addr['last_packets'],
                                                       addr['ewma_rssi'],
                                                       addr['sma_rssi'])

            with open(filename, 'a') as file_d:
                file_d.write(line)

    def ncqm_callback(self, poller):
        """Called when a UCQM response is received from a WTP."""

        import time

        filename = "ncqm_%s_%u_%s.csv" % (poller.block.addr,
                                          poller.block.channel,
                                          poller.block.band)

        for addr in poller.maps.values():

            line = "%f,%s,%.2f,%.2f,%u,%.2f,%.2f\n" % (time.time(),
                                                       addr['addr'],
                                                       addr['last_rssi_avg'],
                                                       addr['last_rssi_std'],
                                                       addr['last_packets'],
                                                       addr['ewma_rssi'],
                                                       addr['sma_rssi'])

            with open(filename, 'a') as file_d:
                file_d.write(line)


def launch(tenant, addrs=DEFAULT_ADDRESS, period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return RSSITracker(tenant, addrs=addrs, every=period)
