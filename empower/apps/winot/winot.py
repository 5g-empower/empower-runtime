#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

"""WiNot App."""

import random

from empower.core.image import Image
from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.datatypes.etheraddress import EtherAddress

DEFAULT_LVAP = "18:5E:0F:E3:B8:68"

VNF_DUPE_FILTER = """
in_0 -> Classifier(12/bbbb)
 -> Strip(14)
 -> dupe::ScyllaWifiDupeFilter()
 -> WifiDecap()
 -> out_0
"""


class WiNot(EmpowerApp):
    """WiNot App.

    Command Line Parameters:

        tenant_id: tenant id
        max_uplinks: maximum number of uplinks (optinal, default 1)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.winot.winot \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.cppup(callback=self.cpp_up_callback)
        self.wtpup(callback=self.wtp_up_callback)
        self.lvnfjoin(callback=self.lvnf_join_callback)
        self.lvnf = None

    def loop(self):
        """ Periodic job. """

        lvap = self.lvap(self.lvap_addr)

        if not lvap:
            return

        if self.max_uplinks == 1:
            lvap.blocks = lvap.blocks[0]
            lvap.encap = EtherAddress("00:00:00:00:00:00")
            return

        blocks = self.blocks()

        selected = []

        for block in blocks:
            if block.channel == lvap.blocks[0].channel and \
               block.band == lvap.blocks[0].band and block != lvap.blocks[0]:

                selected.append(block)

        selected.sort(key=lambda x: x.ucqm[lvap.addr]['mov_rssi'],
                      reverse=True)

        selected = [lvap.blocks[0]] + selected[0:self.max_uplinks-1]

        if set(lvap.blocks) == set(selected):
            return

        lvap.blocks = selected

        lvap.encap = EtherAddress("66:C3:CE:D9:05:51")
        rules = (lvap.addr.to_str(), lvap.encap.to_str())

        if self.lvnf:
            match = "dl_src=%s,dl_dst=%s" % rules
            lvap.ports[0].next[match] = self.lvnf.ports[0]

    def lvnf_join_callback(self, lvnf):
        """Called when an LVNF joins the tenant."""

        if not self.lvnf:
            self.lvnf = lvnf
        else:
            lvnf.stop()

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        for block in wtp.supports:
            self.ucqm(block=block, every=self.every)

    def cpp_up_callback(self, cpp):
        """Called when a new CPP connects to the controller."""

        img = Image(vnf=VNF_DUPE_FILTER)
        self.spawn_lvnf(img, cpp)

    @property
    def max_uplinks(self):
        """Return max_uplinks."""

        return self.__max_uplinks

    @max_uplinks.setter
    def max_uplinks(self, value):
        """Set max_uplinks."""

        self.__max_uplinks = int(value)

    @property
    def lvap_addr(self):
        """Return lvap_addr."""

        return self.__lvap_addr

    @lvap_addr.setter
    def lvap_addr(self, value):
        """Set lvap_addr."""

        self.__lvap_addr = EtherAddress(value)


def launch(tenant_id, lvap_addr=DEFAULT_LVAP, max_uplinks=1, period=5000):
    """Initialize the module.`"""

    return WiNot(tenant_id=tenant_id, lvap_addr=lvap_addr,
                 max_uplinks=max_uplinks)
