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

"""Survey App."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.core.resourcepool import BANDS
from empower.datatypes.etheraddress import EtherAddress

DEFAULT_ADDRESS = "ff:ff:ff:ff:ff:ff"


class Survey(EmpowerApp):
    """Survey App.

    Command Line Parameters:

        tenant_id: tenant id
        addr: the address to be tracked (optional, default ff:ff:ff:ff:ff:ff)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.survey.survey \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26
    """

    def __init__(self, **kwargs):
        self.__addr = None
        EmpowerApp.__init__(self, **kwargs)
        self.links = {}
        self.wtpup(callback=self.wtp_up_callback)

    @property
    def addr(self):
        """Return addr."""

        return self.__addr

    @addr.setter
    def addr(self, value):
        """Set addr."""

        self.__addr = EtherAddress(value)

    def wtp_up_callback(self, wtp):
        """New WTP."""

        for block in wtp.supports:
            self.summary(addr=self.addr,
                         block=block,
                         period=1000,
                         callback=self.summary_callback)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Summary """

        out = super().to_dict()
        out['links'] = self.links
        return out

    def summary_callback(self, summary):
        """ New stats available. """

        self.log.info("New summary from %s addr %s frames %u", summary.block,
                      summary.addr, len(summary.frames))

        # per block log
        filename = "survey_%s_%u_%s.csv" % (summary.block.addr,
                                            summary.block.channel,
                                            BANDS[summary.block.band])

        for frame in summary.frames:

            line = "%u,%g,%s,%d,%u,%s,%s,%s,%s,%s\n" % \
                (frame['tsft'], frame['rate'], frame['rtype'], frame['rssi'],
                 frame['length'], frame['type'], frame['subtype'],
                 frame['ra'], frame['ta'], frame['seq'])

            with open(filename, 'a') as file_d:
                file_d.write(line)

        # per link log
        for frame in summary.frames:

            link = "%s_%s_%u_%s" % (frame['ta'], summary.block.addr,
                                    summary.block.channel,
                                    BANDS[summary.block.band])

            filename = "link_%s.csv" % link

            if link not in self.links:
                self.links[link] = {}

            if frame['rssi'] not in self.links[link]:
                self.links[link][frame['rssi']] = 0

            self.links[link][frame['rssi']] += 1

            line = "%u,%g,%s,%d,%u,%s,%s,%s,%s,%s\n" % \
                (frame['tsft'], frame['rate'], frame['rtype'], frame['rssi'],
                 frame['length'], frame['type'], frame['subtype'],
                 frame['ra'], frame['ta'], frame['seq'])

            with open(filename, 'a') as file_d:
                file_d.write(line)


def launch(tenant_id, addr=DEFAULT_ADDRESS, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return Survey(tenant_id=tenant_id, addr=addr, every=every)
