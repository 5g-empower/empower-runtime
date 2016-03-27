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

"""Application tracking pool-wide power consumption."""

import time

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class PowerTracker(EmpowerApp):
    """Application tracking pool-wide power consumption.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.powertracker.powertracker:$ID

    """

    def __init__(self, tenant, **kwargs):

        self.filename = "./powertracker.csv"
        EmpowerApp.__init__(self, tenant, **kwargs)

    def loop(self):
        """ Periodic job. """

        power = 0.0

        for wtp in self.wtps():
            if not wtp.feed:
                continue
            for datastream in wtp.feed.datastreams.values():
                if datastream['id'] == 'power':
                    power += datastream['current_value']

        line = "%u %f\n" % (time.time(), power)

        with open(self.filename, 'a') as file_d:
            file_d.write(line)


def launch(tenant, filename="./powertracker.csv", period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return PowerTracker(tenant, filename=filename, every=period)
