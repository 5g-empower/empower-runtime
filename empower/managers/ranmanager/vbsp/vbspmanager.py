#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""VBSP RAN Manager."""

import empower.managers.ranmanager.vbsp as vbsp

from empower.managers.ranmanager.ranmanager import RANManager
from empower.managers.ranmanager.vbsp.vbshandler import VBSHandler
from empower.managers.ranmanager.vbsp.vbspconnection import VBSPConnection
from empower.managers.ranmanager.vbsp.vbs import VBS


DEFAULT_PORT = 5533


class VBSPManager(RANManager):
    """VBSP RAN Manager

    Parameters:
        port: the port on which the TCP server should listen (optional,
            default: 5533)
    """

    HANDLERS = [VBSHandler]

    def __init__(self, context, service_id, port):

        super().__init__(context=context,
                         service_id=service_id,
                         device_type=VBS,
                         connection_type=VBSPConnection,
                         proto=vbsp,
                         port=port)

        self.ueqs = {}


def launch(context, service_id, port=DEFAULT_PORT):
    """ Initialize the module. """

    return VBSPManager(context=context, service_id=service_id, port=port)
