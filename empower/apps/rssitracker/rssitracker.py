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

"""Application implementing an rssi tracker."""

from empower.datatypes.etheraddress import EtherAddress
from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD

DEFAULT_ADDRESS = "ff:ff:ff:ff:ff:ff"


class RSSITracker(EmpowerApp):
    """Application implementing an rssi tracker.

    Command Line Parameters:

        tenant_id: tenant id
        addrs: the addresses to be tracked (optional, default
            ff:ff:ff:ff:ff:ff)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.rssitracker.rssitracker \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        self.__addrs = None
        EmpowerApp.__init__(self, **kwargs)
        self.wtpup(callback=self.wtp_up_callback)

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

            self.ucqm(block=block,
                      every=self.every,
                      callback=self.ucqm_callback)

            self.ncqm(block=block,
                      every=self.every,
                      callback=self.ncqm_callback)

    def ucqm_callback(self, poller):
        """Called when a UCQM response is received from a WTP."""

        import time

        filename = "ucqm_%s_%u_%s.csv" % (poller.block.addr,
                                          poller.block.channel,
                                          poller.block.band)

        for addr in poller.maps.values():

            line = "%f,%s,%.2f,%.2f,%u,%.2f\n" % (time.time(),
                                                  addr['addr'],
                                                  addr['last_rssi_avg'],
                                                  addr['last_rssi_std'],
                                                  addr['last_packets'],
                                                  addr['mov_rssi'])

            with open(filename, 'a') as file_d:
                file_d.write(line)

    def ncqm_callback(self, poller):
        """Called when a UCQM response is received from a WTP."""

        import time

        filename = "ncqm_%s_%u_%s.csv" % (poller.block.addr,
                                          poller.block.channel,
                                          poller.block.band)

        for addr in poller.maps.values():

            line = "%f,%s,%.2f,%.2f,%u,%.2f\n" % (time.time(),
                                                  addr['addr'],
                                                  addr['last_rssi_avg'],
                                                  addr['last_rssi_std'],
                                                  addr['last_packets'],
                                                  addr['mov_rssi'])

            with open(filename, 'a') as file_d:
                file_d.write(line)


def launch(tenant_id, addrs=DEFAULT_ADDRESS, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return RSSITracker(tenant_id=tenant_id, addrs=addrs, every=every)
