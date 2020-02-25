#!/usr/bin/env python3
#
# Copyright (c) 2020 Cristina Costa
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

import empower.managers.lommmanager.lnsdp as lnsdp

from empower.managers.lommmanager.wsmanager               import WSManager
from empower.managers.lommmanager.lnsdp.lnsshandler       import LNSsHandler
from empower.managers.lommmanager.lnsdp.lgtwshandler      import LGTWsHandler
from empower.managers.lommmanager.lnsdp.lnsdpmainhandler  import LNSDPMainHandler
from empower.managers.lommmanager.lnsdp.lns import LNS
from empower.datatypes.eui64 import EUI64

__author__     = "Cristina E. Costa"
__copyright__  = "Copyright 2019, FBK (https://www.fbk.eu)"
__credits__    = ["Cristina E. Costa"]
__license__    = "Apache License, Version 2.0"
__version__    = "1.0.0"
__maintainer__ = "Cristina E. Costa"
__email__      = "ccosta@fbk.eu"
__status__     = "Dev"

class LNSDPManager(WSManager):
    """LNS Discovery Server Manager

    Parameters:
        port: the port on which the WS server should listen (optional,
            default: 6038)
    """
    DEFAULT_PORT = 6038
    LABEL        = "LNS Discovery Server"
    HANDLERS     = [LNSsHandler, LGTWsHandler]
    WSHANDLERS   = [LNSDPMainHandler]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lnss = {}
        
    @property
    def lgtws(self):
        """Return the lgtws."""
        lgtws = {}
        for lns_euid in self.lnss:
            lns = self.lnss[lns_euid]
            for lgtw_euid in lns.lgtws: 
                if lgtw_euid not in lgtws:
                    lgtws[lgtw_euid] = []                
                lgtws[lgtw_euid].append(lns_euid)
        return lgtws
        
    def start(self):
        """Start control loop."""
        super().start()     
        """ retrieve data from the db """   
        for lns in LNS.objects:
            self.lnss[lns.euid] = lns
                
    def add_lns(self, lns_euid, **kwargs):
        """Add new lns."""
        try:
            lns_euid = EUI64(lns_euid).id6
        except:
            raise ValueError("LNS euid (lns_euid) not valid")

        desc  = kwargs.get("desc","Generic LNS")
        uri   = kwargs.get("uri")
        lgtws = kwargs.get("lgtws",[])
        if lgtws:
            try:
                lgtws    = [EUI64(lgtw).id6 for lgtw in lgtws]
            except:
                raise ValueError("lGTW euid (lgtw_euid=%s) not valid"%str(lgtws))

        if lns_euid in self.lnss:
            raise ValueError("LNS %s already registered in the LNS Discovery Server" % lns_euid)
       
        if lgtws:
            lns = LNS(uri=uri, euid=lns_euid, desc=desc, lgtws=lgtws).save()
        else:
            lns = LNS(uri=uri, euid=lns_euid, desc=desc).save()
        self.lnss[lns_euid] = lns
       
        return self.lnss[lns_euid]

    def update_lns(self, lns_euid, **kwargs):
        """Update lns data."""
        lns_euid = EUI64(lns_euid).id6
        desc     = kwargs.get("desc")
        uri      = kwargs.get("uri")
        lgtws    = [EUI64(lgtw).id6 for lgtw in kwargs.get("lgtws",[])]
        
        try:
            lns = self.lnss[lns_euid]
        except KeyError:
            raise KeyError("%s not registered, register lns first" % lns_euid)
        except:
            raise

        if lgtws:
            for lgtw in lgtws:
                if lgtw not in self.lnss.lgtws:
                    lns.lgtws.append(lgtws)
        
        if uri:
            lns.uri = uri

        if desc:
            lns.desc = desc

        lns.save()

    def remove_lns(self, lns_euid):
        """Remove LNS."""
        if lns_euid not in self.lnss:
            raise ValueError("%s not registered" % lns_euid)
        lns = self.lnss[lns_euid]
        lns.delete()
        del self.lnss[lns_euid]

    def remove_all_lnss(self):
        """Remove all LNSs."""
        for euid in list(self.lnss):
            self.remove_lns(EUI64(euid).id6)
            
    def add_lgtw(self,  **kwargs):
        """Add new lgtw."""
        if 'lns_euid' not in kwargs:
            raise ValueError("lns_euid must be present")
        if 'lgtw_euid' not in kwargs:
            raise ValueError("lgtw_euid must be present")
            
        lns_euid  = EUI64(kwargs.get("lns_euid")).id6
        lgtw_euid = EUI64(kwargs.get("lgtw_euid")).id6
        try:
            lns = self.lnss[lns_euid]
        except KeyError:
            raise KeyError("%s not registered, register lns first" % lns_euid)
        except:
            raise

        if lgtw_euid not in lns.lgtws:
            if lns.lgtws:
                lns.lgtws.append(lgtw_euid)
            else:
                lns.lgtws = [lgtw_euid]
            lns.save()
            self.lnss[euid] = lns
            
        return lgtw_euid

    def remove_lgtw_from_lns(self, lgtw_euid, lns_euid):
        """Remove GTW from an LNS."""
        try: 
            lns = self.lnss[lns_euid]
        except KeyError:
            raise ValueError("%s not registered" % lns_euid)
        except:
            raise              
        
        if lgtw_euid in lns.lgtws:
            lns.lgtws.remove(lgtw_euid)
            lns.save()
            self.lnss[lns_euid] = lns
            
    def remove_lgtw(self, lgtw_euid, lns_euid = None):
        """Remove GTW (is an LNS is not specified, remove for all)."""
        if lns_euid:
            self.remove_lgtw_from_lns(lgtw_euid, lns_euid)
        else:
            for lns_euid in self.lnss:
                self.remove_lgtw_from_lns(lgtw_euid, lns_euid)

def launch(**kwargs):
    """Start LNS Discovery Server Module."""
    return LNSDPManager(**kwargs)
