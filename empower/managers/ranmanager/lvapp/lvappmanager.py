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

"""LVAPP RAN Manager."""

import empower.managers.ranmanager.lvapp as lvapp

from empower.managers.ranmanager.ranmanager import RANManager
from empower.managers.ranmanager.lvapp.wtphandler import WTPHandler
from empower.managers.ranmanager.lvapp.lvaphandler import LVAPHandler
from empower.managers.ranmanager.lvapp.lvappconnection import LVAPPConnection
from empower.core.wtp import WTP

DEFAULT_PORT = 4433


class LVAPPManager(RANManager):
    """LVAPP RAN Manager

    Parameters:
        port: the port on which the TCP server should listen (optional,
            default: 4433)
    """

    HANDLERS = [LVAPHandler, WTPHandler]

    def __init__(self, **kwargs):

        if 'port' not in kwargs:
            kwargs['port'] = DEFAULT_PORT

        super().__init__(device_type=WTP,
                         connection_type=LVAPPConnection,
                         proto=lvapp,
                         **kwargs)

        self.lvaps = {}
        self.vaps = {}


def launch(**kwargs):
    """Start LVAPP Server Module."""

    return LVAPPManager(**kwargs)
