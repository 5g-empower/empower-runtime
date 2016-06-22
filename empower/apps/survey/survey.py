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
            self.summary(addr=self.addr, block=block,
                         callback=self.summary_callback)

    def summary_callback(self, summary):
        """ New stats available. """

        self.log.info("New summary from %s addr %s frames %u", summary.block,
                      summary.addr, len(summary.frames))


def launch(tenant_id, addr=DEFAULT_ADDRESS, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return Survey(tenant_id=tenant_id, addr=addr, every=every)
