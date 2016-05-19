#!/usr/bin/env python3
#
# Copyright (c) 2016, Roberto Riggio
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

"""Radio Maps Poller App."""

from empower.apps.pollers.poller import Poller
from empower.core.app import DEFAULT_PERIOD


class MapsPoller(Poller):
    """Radio Maps Poller App.

    Command Line Parameters:

        tenant_id: tenant id
        filepath: path to file for statistics (optional, default ./)
        every: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.pollers.mapspoller --tenant_id=$ID

    """

    def __init__(self, **kwargs):
        Poller.__init__(self, **kwargs)
        self.wtpup(callback=self.wtp_up_callback)

    def wtp_up_callback(self, wtp):
        """ Called when a new WTP connects to the controller"""

        for block in wtp.supports:

            self.ucqm(block=block, every=self.every,
                      callback=self.ucqm_callback)

            self.ncqm(block=block, every=self.every,
                      callback=self.ncqm_callback)

    def ucqm_callback(self, ucqm):
        """ New stats available. """

        self.log.info("New UCQM received from %s" % ucqm.block)

    def ncqm_callback(self, ucqm):
        """ New stats available. """

        self.log.info("New NCQM received from %s" % ucqm.block)


def launch(tenant_id, filepath="./", every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return MapsPoller(tenant_id=tenant_id, filepath=filepath, every=every)
