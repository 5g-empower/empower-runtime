#!/usr/bin/env python3
#
# Copyright (c) 2019, CREATE-NET FBK, Trento, Italy
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

# TODO ADD REFERENCE TO ALLOWED DEVICES
"""LoRaWAN NS Discovery WS Server Manager."""

import empower.managers.lommmanager.lnsp as lnsp

from empower.managers.lommmanager.wsmanager               import WSManager

from empower.managers.lommmanager.lnsp.lenddevshandler    import LEndDevsHandler
from empower.managers.lommmanager.lnsp.lgtwshandler       import LGTWsHandler
from empower.managers.lommmanager.lnsp.lnspmainhandler    import LNSPMainHandler

from empower.managers.lommmanager.lnsp.lorawandevice      import LoRaWANEndDev
from empower.managers.lommmanager.lnsp.lorawangtw         import LoRaWANgtw

from empower.datatypes.eui64    import EUI64 
from empower.managers.lommmanager.lnsp.lgtws_default_confs import LGTW_CONFIG_EU863_6CH
from empower.managers.lommmanager.lnsp.lenddevs_confs      import LEND_DEVS


__author__     = "Cristina E. Costa"
__copyright__  = "Copyright 2019, FBK (https://www.fbk.eu)"
__credits__    = ["Cristina E. Costa"]
__license__    = "Apache License, Version 2.0"
__version__    = "1.0.0"
__maintainer__ = "Cristina E. Costa"
__email__      = "ccosta@fbk.eu"
__status__     = "Dev"


class LNSPManager(WSManager):
    """LNS Discovery Server Manager

    Parameters:
        port: the port on which the WS server should listen (optional,
            default: 6039)
    """
    DEFAULT_PORT = 6039
    LABEL        = "LNS Discovery Server"
    HANDLERS     = [LGTWsHandler, LEndDevsHandler]
    WSHANDLERS   = [LNSPMainHandler]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lenddevs = {}
        # self.lenddevs = lnsp.LEND_DEVS
        for lenddev in LEND_DEVS:
            self.add_lenddev(**LEND_DEVS[lenddev])
        self.lgtws = {}
        
    def start(self):
        """Start control loop."""
        super().start()     
        """ retrieve data from the db """   
        for dev in LoRaWANEndDev.objects:
            self.lenddevs[str(dev.devEUI)] = dev
        for lgtw in LoRaWANgtw.objects:
            self.lgtws[str(lgtw.lgtw_euid)]   = lgtw
            
    def add_lenddev(self, devEUI, **kwargs):
        """Add new End Device."""
        params = {}
        # joinEUI = kwargs.get("joinEUI")
        # if joinEUI:
        #     params["joinEUI"] = EUI64(joinEUI)
        
        devEUI=devEUI.upper()
        if devEUI in self.lenddevs:
            raise ValueError("End Device %s already registered in the LNS Server" % devEUI)
        lenddev = LoRaWANEndDev(
            devEUI=devEUI, 
            devAddr=kwargs.get("devAddr").upper() if isinstance(kwargs.get("devAddr"), str) else None, 
            desc=kwargs.get("desc","Generic End Device"), 
            joinEUI=kwargs.get("joinEUI").upper() if isinstance(kwargs.get("joinEUI"), str) else None, 
            nwkKey=kwargs.get("nwkKey").upper() if isinstance(kwargs.get("nwkKey"), str) else None, 
            appKey=kwargs.get("appKey").upper() if isinstance(kwargs.get("appKey"), str) else None, 
            nwkSKey=kwargs.get("nwkSKey").upper() if isinstance(kwargs.get("nwkSKey"), str) else None, 
            appSKey=kwargs.get("appSKey").upper() if isinstance(kwargs.get("appSKey"), str) else None, 
            activation=kwargs.get("activation").upper if kwargs.get("activation").upper in  ["OTAA","ABP"] else None,
            fcntWidth=kwargs.get("FCntWidth").lower if kwargs.get("FCntWidth").lower in ["16bit", "32bit"] else None, # 16bit or 32bit
            # fcntChecks=kwargs.get("FCntChecks") if isinstance(kwargs.get("FCntChecks"), bool) else None,
            location=kwargs.get("location") if isinstance(kwargs.get("location"), dict) else None,
            payloadFormat=kwargs.get("payloadFormat").capitalize() if isinstance(kwargs.get("payloadFormat"), str) else None
            ).save()
        self.lenddevs[devEUI] = lenddev
        return self.lenddevs[devEUI]
            
    def update_lenddev(self, devEUI, **kwargs):
        """Add new End Device."""
        desc    = kwargs.get("desc","Generic End Device")
        joinEUI = str(EUI64(kwargs.get("joinEUI","")))
        appKey  = kwargs.get("appKey")
        nwkKey  = kwargs.get("nwkKey")
        
        try:
            lenddev = self.lenddevs[devEUI]
        except KeyError:
            raise KeyError("End Device %s not registered in the LNS Server" % lgtw_devEUI)
        except:
            raise
        if joinEUI:
            lenddev.joinEUI = joinEUI
        if appKey:
            lenddev.appKey  = appKey
        if nwkKey:
            lenddev.nwkKey  = nwkKey
        if desc:
            lenddev.desc    = desc

        lenddev.save()
        self.lenddevs[devEUI] = lenddev
        return self.lenddevs[devEUI]

    def remove_lenddev(self, devEUI):
        """Remove End Device."""
        devEUI = str(EUI64(devEUI))
        if devEUI not in self.lenddevs:
            raise KeyError("End Device %s not registered" % devEUI)
        lenddev = self.lenddevs[devEUI]
        lenddev.delete()
        del self.lenddevs[devEUI]

    def remove_all_lenddevs(self):
        """Remove all LNSs."""
        for devEUI in list(self.lenddevs):
            self.remove_lenddev(devEUI)
            
    def add_lgtw(self, lgtw_euid, **kwargs):
        desc         = kwargs.get("desc","Generic GTW")
        name         = kwargs.get("name","lgtw")
        owner        = str(EUI64(kwargs.get("owner", lnsp.DEFAULT_OWNER)))
        lgtw_config  = kwargs.get("lgtw_config", LGTW_CONFIG_EU863_6CH)

        if lgtw_euid in self.lgtws:
            raise ValueError("GTW %s already registered in the LNS Server" % lgtw_euid)

        self.lgtws[lgtw_euid] = LoRaWANgtw(
            lgtw_euid=lgtw_euid, 
            desc=desc, owner=owner, 
            lgtw_config=lgtw_config, name=name).save()
        
        return self.lgtws[lgtw_euid]
            
    def update_lgtw(self, lgtw_euid, **kwargs):
        desc         = kwargs.get("desc","Generic GTW")
        name         = kwargs.get("name","lgtw")
        owner        = str(EUI64(kwargs.get("owner", lnsp.DEFAULT_OWNER)))
        lgtw_config  = kwargs.get("lgtw_config", LGTW_CONFIG_EU863_6CH)

        if lgtw_euid not in self.lgtws:
            raise ValueError("GTW %s not registered in the LNS Server" % lgtw_euid)

        try:
            lgtw = self.lgtws[lgtw_euid]
        except KeyError:
            raise KeyError("%s not registered, register lgtw first" % lgtw_euid)
        except:
            raise
        if owner:
            name.lgtw_config = owner
        if lgtw_config:
            name.lgtw_config = lgtw_config
        if name:
            name.uri = name
        if desc:
            lgtw.desc = desc

        self.lgtws[lgtw_euid] = lgtw.save()
        
        return self.lgtws[lgtw_euid]

    def remove_lgtw(self, lgtw_euid):
        """Remove GTW."""
        lgtw_euid = EUI64(lgtw_euid).eui
        if lgtw_euid not in self.lgtws:
            raise KeyError("GTW %s not registered" % lgtw_euid)
        lgtw = self.lgtws[lgtw_euid]
        lgtw.delete()
        del self.lgtws[lgtw_euid]

    def remove_all_lgtws(self):
        """Remove all GTWs."""
        for lgtw_euid in list(self.lgtws):
            self.remove_lgtw(lgtw_euid)
            


def launch(**kwargs):
    """Start LNS Discovery Server Module."""

    return LNSPManager(**kwargs)
