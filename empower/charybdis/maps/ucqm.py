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

"""User channel quality map module."""

from empower.core.module import bind_module
from empower.core.restserver import RESTServer
from empower.charybdis.lvapp.lvappserver import LVAPPServer
from empower.charybdis.maps.maps import MapsHandler
from empower.charybdis.maps.maps import MapsWorker
from empower.charybdis.maps.maps import Maps
from empower.charybdis.maps.maps import POLLER_RESP_MSG

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class UCQM(Maps):
    pass


class UCQMHandler(MapsHandler):
    pass


class UCQMWorker(MapsWorker):

    MODULE_NAME = "ucqm"
    MODULE_HANDLER = UCQMHandler
    MODULE_TYPE = UCQM

    POLLER_REQ_MSG_TYPE = 0x25
    POLLER_RESP_MSG_TYPE = 0x26

bind_module(UCQMWorker)


def launch():
    """ Initialize the module. """

    lvap_server = RUNTIME.components[LVAPPServer.__module__]
    rest_server = RUNTIME.components[RESTServer.__module__]

    worker = UCQMWorker(rest_server)
    lvap_server.register_message(worker.POLLER_RESP_MSG_TYPE,
                                 POLLER_RESP_MSG,
                                 worker.handle_poller_response)

    return worker
