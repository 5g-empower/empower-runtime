#!/usr/bin/env python3
#
# Copyright (c) 2018 Estefania Coronado
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

"""IGMP traffic module."""

import ipaddress

from datetime import datetime

from construct import UBInt8
from construct import UBInt32
from construct import Bytes
from construct import Struct

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.lvapp.lvappserver import ModuleLVAPPEventWorker
from empower.core.module import ModuleTrigger

from empower.main import RUNTIME

PT_IGMP_REPORT = 0x48

IGMP_REPORT = Struct("igmp_report", UBInt8("version"),
                     UBInt8("type"),
                     UBInt32("length"),
                     UBInt32("seq"),
                     Bytes("wtp", 6),
                     Bytes("sta", 6),
                     Bytes("mcast_addr", 4),
                     UBInt8("igmp_type"))


class IGMPReport(ModuleTrigger):
    """ IGMPReport trigger object. """

    MODULE_NAME = "igmp_report"
    REQUIRED = ['module_type', 'worker', 'tenant_id']

    def __init__(self):
        super().__init__()

        # data structures
        self.events = []

    def to_dict(self):
        """Return a JSON-serializable object."""

        out = super().to_dict()
        out['events'] = self.events
        return out

    def handle_response(self, response):
        """ Handle an INCOM_MCAST_REQUEST event.
        Args:
            wtp, an WTP object
        Returns:
            None
        """

        event = \
            {'wtp': EtherAddress(response.wtp),
             'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
             'sta': EtherAddress(response.sta),
             'mcast_addr': ipaddress.IPv4Address(response.mcast_addr),
             'igmp_type': response.igmp_type}

        self.events.append(event)

        self.handle_callback(self)


class IgmpReportWorker(ModuleLVAPPEventWorker):
    """ Counter worker. """

    pass


def igmp_report(**kwargs):
    """Create a new module."""

    return RUNTIME.components[IgmpReportWorker.__module__].add_module(**kwargs)


def app_igmp_report(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return igmp_report(**kwargs)


setattr(EmpowerApp, IGMPReport.MODULE_NAME, app_igmp_report)


def launch():
    """Initialize the module."""

    return IgmpReportWorker(IGMPReport, PT_IGMP_REPORT, IGMP_REPORT)
