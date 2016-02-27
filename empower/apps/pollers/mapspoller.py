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
from empower.apps.pollers.poller import DEFAULT_POLLING
from empower.core.app import DEFAULT_PERIOD
from empower.events.wtpup import wtpup
from empower.maps.ucqm import ucqm
from empower.maps.ncqm import ncqm

import empower.logger
LOG = empower.logger.get_logger()


class MapsPoller(Poller):
    """Radio Maps Poller App.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ID="52313ecb-9d00-4b7d-b873-b55d3d9ada26"
        ./empower-runtime.py apps.pollers.mapspoller:$ID

    """

    def __init__(self, tenant, **kwargs):

        Poller.__init__(self, tenant, **kwargs)

        wtpup(tenant_id=self.tenant.tenant_id, callback=self.wtp_up_callback)

    def wtp_up_callback(self, wtp):
        """ Called when a new WTP connects to the controller"""

        for block in wtp.supports:

            if block.black_listed:
                continue

            ucqm(block=block,
                 tenant_id=self.tenant.tenant_id,
                 every=self.polling,
                 callback=self.ucqm_callback)

            ncqm(block=block,
                 tenant_id=self.tenant.tenant_id,
                 every=self.polling,
                 callback=self.ncqm_callback)

    def ucqm_callback(self, ucqm):
        """ New stats available. """

        LOG.info("New UCQM received from %s" % ucqm.block)

    def ncqm_callback(self, ucqm):
        """ New stats available. """

        LOG.info("New NCQM received from %s" % ucqm.block)


def launch(tenant,
           filepath="./",
           polling=DEFAULT_POLLING,
           period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return MapsPoller(tenant,
                      filepath=filepath,
                      polling=polling,
                      every=period)
