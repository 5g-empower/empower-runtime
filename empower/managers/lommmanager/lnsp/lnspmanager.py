#!/usr/bin/env python3
#
# Copyright (c) 2020 Fondazione Bruno Kessler
# Author(s): Cristina Costa (ccosta@fbk.eu)
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
"""LNS Protocol Server Manager.

Manages the Web Socket connection with the Semtech Basic Station LoRaWAN GTWs.
"""
import json

import empower.managers.lommmanager.lnsp as lnsp

from empower.managers.lommmanager.wsmanager import WSManager

from empower.managers.lommmanager.lnsp.lenddevshandler import LEndDevsHandler
from empower.managers.lommmanager.lnsp.lgtwshandler import LGTWsHandler
from empower.managers.lommmanager.lnsp.lnspmainhandler import LNSPMainHandler

from empower.managers.lommmanager.lnsp.lorawandevice import LoRaWANEndDev
from empower.managers.lommmanager.lnsp.lorawangtw import LoRaWANgtw

from empower.core.eui64 import EUI64

JSON_FILE = "empower/managers/lommmanager/lnsp/lgtws_default_conf.json"

# NOTE:
# The LNS responds to a version message with a router_config message
# to specify a channel plan for the Station and define
# some basic operation modes
# BASIC OPERATION MODES:
#     'JoinEui': list of pairs of integer values encoding ranges of join EUIs.
#                [[INT,INT],..]
#                The JoinEui unique ID of the Join server, 64 bit number.
#                Used to filter LoRa frames received by Station.
#                Join request frames will be dropped by Station unless the
#                field JoinEui in the message satisfies the condition
#                BegEui<=JoinEui<=EndEui for at least one pair [BegEui,EndEui].
#     'NetID': list of NetID values that are accepted by LNS [INT,..]
#              The NetID is a 24-bit value used for identifying LoRaWAN
#              network, have a non-collaborating network,
#              you can use the 0x000000 or 0x000001.
#              Used to filter LoRa frames received by Station.
#     'nocca': disable clear channel assessment (bool),
#              used only by debug builds of Station
#     'nodwell': disable dwell-time (bool),
#                used only by debug builds of Station
#     'nodc': disable duty sycle (bool),
#             used only by debug builds of Station,
# CHANNEL PLAN:
#     'region': base region name of channel plan (e.g.'EU863'). (str)
#               the Basic Station controls certain regulatory behaviors such as
#               clear channel assessment, duty-cycle and dwell-time
#               limitations. Valid names are compatible with the names of
#               the LoRaWAN Regional Parameters specification,
#               except the end frequency is dropped (e.g., EU863 and US902).
#     'hwspec': 'sx1301/**N**' (str)
#               what concentrator hardware is needed to operate the channel
#               plan. The assigned string MUST have the following form:
#                             sx1301/**N**
#               where N denotes the number of SX1301 concentrator chips
#               required to operate the channel plan. Station will check this
#               requirement against its hardware capabilities.
#     'freq_range': lower and upper boundaries of the available spectrum for
#                   the region set. [INT,INT] -->  min, max (hz)
#                   Station will NOT allow downlink transmissions outside of
#                   this frequency range.
#     'DRs': available data rates of the channel plan
#            [[INT,INT,INT],..] --> SF, BW, dnonly
#            It is array of 16 entries with each entry being an array of three
#            integers encoding:
#                 the spreading factor SF (7..12 for LoRa, or 0 for FSK),
#                 the bandwidth BW (125, 250, or 500 for LoRa, ignored for FSK)
#                 a DNONLY flag (1 if the DR is valid for downlink frames only,
#                                0 otherwise).
#            TO CHECK - depends on regional settings
#     'upchannels': [[868100000, 0, 5],
#                    [868300000, 0, 5],
#                    [868500000, 0, 5],
#                    [868850000, 0, 5],
#                    [869050000, 0, 5],
#                    [869525000, 0, 5]]
#                    TO CHECK - depends on regional settings
#     'sx1301_conf': defines how the channel plan maps to the individual
#                    SX1301 chips. Its value is an array of SX1301CONF objects.
#                    [SX1301CONF,..].
#                    The number of array elements MUST be in accordance with
#                    the value of the field hwspec.
#                    The layout of a SX1301CONF object looks like this:
#                     {
#                     "radio_0": { .. } // same structure as radio_1
#                     "radio_1": {
#                         "enable": BOOL,
#                         "freq"  : INT
#                     },
#                     "chan_FSK": {
#                         "enable": BOOL,
#                         "radio": 0|1,
#                         "if": INT
#                     },
#                     "chan_Lora_std": {
#                         "enable": BOOL,
#                         "radio": 0|1,
#                         "if": INT,
#                         "bandwidth": INT,
#                         "spread_factor": INT
#                     },
#                     "chan_multiSF_0": { .. }
#                     // _0 .. _7 all have the same structure
#                     ..
#                     "chan_multiSF_7": {
#                         "enable": BOOL,
#                         "radio": 0|1,
#                         "if": INT
#                     }
#                     }

# OTHER PARAMETERS (TO BE CHECKED) maybe depends on Basic Station version...
#     'bcning': null,
#     'max_eirp': 16.0,
#     'protocol': 1,
#     'config': {},

#     'regionid': points to region in regions.json which
#                 defines DRs and upchannels

#  In the station2pkfwd, each region is defined with its regionid, name and
#  configuration (region information is loaded from regions.yaml).
#  https://github.com/lorabasics/basicstation/blob/master/examples/station2pkfwd/regions.yaml

#  upchannels and DRs are injected into the router configurations which
#  references this region with the regionid.

#  Routers are configured in router-<ID>.yaml files (in station2pkfwd):
#  each router configuration is merged with the region information and
#  sent to Station on connect.
# https://github.com/lorabasics/basicstation/blob/master/examples/station2pkfwd/router_config.py
# https://github.com/lorabasics/basicstation/blob/master/examples/station2pkfwd/router-1.yaml
#  Region and router configurations are loaded at startup.

DEFAULT_PORT = 6039


class LNSPManager(WSManager):
    """LNS Protocol Server Manager.

    Parameters:
        port: the port on which the WS server should listen (optional,
            default: 6039)
    """

    HANDLERS = [LGTWsHandler, LEndDevsHandler]
    WSHANDLERS = [LNSPMainHandler]
    lenddevs = {}
    lgtws = {}

    def __init__(self, **kwargs):
        """Init LNS Protocol Manager."""
        super().__init__(**kwargs)
        with open(JSON_FILE, 'r') as fin:
            lgtw_confs = json.load(fin)
        self.lgtw_settings = lgtw_confs["LGTW_CONFIG_EU863_6CH"]

    def start(self):
        """Start control loop."""
        super().start()
        # retrieve data from the db
        for dev in LoRaWANEndDev.objects:
            self.lenddevs[dev.dev_eui] = dev
        for lgtw in LoRaWANgtw.objects:
            self.lgtws[lgtw.lgtw_euid] = lgtw

    def add_lenddev(self, dev_eui, **kwargs):
        """Add new End Device."""
        dev_eui = EUI64(dev_eui)
        if dev_eui in self.lenddevs:
            raise ValueError(
                "End Device %s already registered in the LNS Server" % dev_eui)
        kwargs["dev_eui"] = dev_eui
        lenddev = LoRaWANEndDev(**kwargs).save()
        self.lenddevs[dev_eui] = lenddev
        return self.lenddevs[dev_eui]

    def update_lenddev(self, dev_eui, **kwargs):
        """Add new End Device."""
        dev_eui = EUI64(dev_eui)
        desc = kwargs.get("desc", "Generic End Device")
        join_eui = EUI64(kwargs.get("joinEUI", ""))
        app_key = kwargs.get("appKey")
        nwk_key = kwargs.get("nwkKey")

        try:
            lenddev = self.lenddevs[dev_eui]
        except KeyError:
            raise KeyError("End Device %s not registered in \
                           the LNS Server" % dev_eui)
        if join_eui:
            lenddev.join_eui = join_eui
        if app_key:
            lenddev.app_key = app_key
        if nwk_key:
            lenddev.nwk_key = nwk_key
        if desc:
            lenddev.desc = desc

        lenddev.save()
        self.lenddevs[dev_eui] = lenddev
        return self.lenddevs[dev_eui]

    def remove_lenddev(self, dev_eui):
        """Remove End Device."""
        dev_eui = EUI64(dev_eui)
        if dev_eui not in self.lenddevs:
            raise KeyError("End Device %s not registered" % dev_eui)
        lenddev = self.lenddevs[dev_eui]
        lenddev.delete()
        del self.lenddevs[dev_eui]

    def remove_all_lenddevs(self):
        """Remove all End Devices from LNS database."""
        for dev_eui in list(self.lenddevs):
            self.remove_lenddev(dev_eui)

    def add_lgtw(self, lgtw_euid, **kwargs):
        """Add lGTW to LNS database."""
        lgtw_euid = EUI64(lgtw_euid)
        name = kwargs.get("name", "BasicStation")
        desc = kwargs.get("desc", "Generic GTW")
        owner = str(kwargs.get("owner", lnsp.DEFAULT_OWNER))
        lgtw_config = kwargs.get("lgtw_config", self.lgtw_settings)

        if lgtw_euid in self.lgtws:
            raise ValueError(
                "GTW %s already registered in the LNS Server" %
                lgtw_euid)

        self.lgtws[lgtw_euid] = LoRaWANgtw(
            lgtw_euid=lgtw_euid,
            desc=desc, owner=owner, name=name,
            lgtw_config=lgtw_config).save()

        return self.lgtws[lgtw_euid]

    def update_lgtw(self, lgtw_euid, **kwargs):
        """Update lGTW in the LNS database."""
        lgtw_euid = EUI64(lgtw_euid)
        desc = kwargs.get("desc")
        name = kwargs.get("name")
        owner = str(kwargs.get("owner"))
        lgtw_config = kwargs.get("lgtw_config")

        if lgtw_euid not in self.lgtws:
            raise ValueError("GTW %s not registered in the \
                             LNS Server" % lgtw_euid)

        try:
            lgtw = self.lgtws[lgtw_euid]
        except KeyError:
            raise KeyError("%s not registered, \
                           register lgtw first" % lgtw_euid)

        if owner:
            lgtw.owner = owner
        if name:
            lgtw.name = name
        if desc:
            lgtw.desc = desc
        if lgtw_config:
            lgtw.lgtw_config = lgtw_config

        self.lgtws[lgtw_euid] = lgtw.save()

        return self.lgtws[lgtw_euid]

    def remove_lgtw(self, lgtw_euid):
        """Remove GTW from LNS database."""
        lgtw_euid = EUI64(lgtw_euid)
        if lgtw_euid not in self.lgtws:
            raise KeyError("GTW %s not registered" % lgtw_euid)
        lgtw = self.lgtws[lgtw_euid]
        lgtw.delete()
        del self.lgtws[lgtw_euid]

    def remove_all_lgtws(self):
        """Remove all GTWs."""
        for lgtw_euid in list(self.lgtws):
            self.remove_lgtw(lgtw_euid)


def launch(context, service_id, port=DEFAULT_PORT):
    """Initialize the module."""
    return LNSPManager(context=context, service_id=service_id, port=port)
