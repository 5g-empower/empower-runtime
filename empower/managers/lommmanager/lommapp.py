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
"""LoMM Test App"""

import datetime, json

import empower.managers.lommmanager.lnsp as lnsp
from   empower.core.app import EApp
from   empower.core.app import EVERY
from   empower.core.launcher import srv_or_die

MODULES  = [lnsp] # List of empower-runtime manager/s used in the app
LABEL    = "Generic LoMM App"

class LoMMApp(EApp):
    """LoMM Basic App.
    Attributes:
        context (Project): Project context in which the app is running (context.services)
        lgtws (dict): Registered LoRaWAN GTWs
        lenddevs (dict): Registered End Devices
        lnss (dict): Registered LNSs
        label (str): Application label (used in the log entries)

    Avaliable LoMM lnsp callbacks:
        LoRaWAN GTW Events Callbacks:
            callback_new_state_transition: called when a GTW changes its state

        Uplink Web Socket Messages Callbacks:            
            callback_version: called when a new Version message arrives      
            callback_jreq: called when a new JREQ Frame arrives   
            callback_updf: called when a new Uplink Data Frame arrives   
            callback_propdf: called when a new Proprietary Frame arrives     
            callback_dntxed: called when a new Transmit Confirmation message arrives  
            callback_timesync: called when a new Timesync message arrives   
            callback_rmtsh: called when a new remote shell message arrives    
        
        Downlink Web Socket Messages Callbacks:            
            callback_router_config: called when a new remote shell message is sent  
            callback_dnmsg: called when a new downlink frame message is sent      
            callback_dnsched: called when a new downlink scheduled frame message is sent 
            callback_dn_timesync: called when a new timesync message is sent            
            callback_rmcmd: called when a new remote command message is sent       
            callback_dn_rmtsh: called when a new remote shell message is sent    
        
        Monitoring Round-trip Times Callbacks:
            callback_rtt_data_rx: called when new RTT data is avaliable
            callback_rtt_query: called when a new RTT query is sent 
            callback_rtt_on: called when RTT query is set to ON 
            callback_rtt_off: called when RTT query is set to OFF 

        Gathering Radio Data Statistics Callbacks:    
            callback_new_radio_data: called when a LoRaWAN Radio GTW radio data is avaliable
    """
        
    def __init__(self, **kwargs):
        """
        Parameters:
            project_id (UUID): the project id
            service_id (UUID): the app id
        """
        self.__label = kwargs.get("label", LABEL)
        self.__modules = kwargs.get("modules", MODULES)
        self.startloop = True
        super().__init__(**kwargs)
                
    def start(self):
        """Run at app start."""
        self.log.info("%s: Registering callbacks", self.label)
        for module in self.__modules:
            module.register_callbacks(self)    
        super().start()
        self.log.info("%s is up!" % self.label)

    def stop(self):
        """Run at app stop."""
        self.log.info("%s: Unegistering callbacks", self.label)
        for module in self.__modules:
            module.unregister_callbacks(self)    
        super().stop()
        
    def loop(self):
        """Periodic job."""
        pass

    @property
    def lgtws(self):
        """Return lGTWs registered in this project context."""
        lnsp_manager  = srv_or_die("lnspmanager")
        return lnsp_manager.lgtws 
        # return self.context.lns_manager.lgtws
        
    @property
    def lenddevs(self):
        """Return lEndDevs registered in this project context."""
        lnsp_manager  = srv_or_die("lnspmanager")
        return lnsp_manager.lenddevs  
        # return self.context.lns_manager.lenddevs

    @property
    def lnss(self):
        """Return LNSs registered in this project context."""
        lnspd_manager = srv_or_die("lnspdmanager")
        return lnspd_manager.lnss 
        # return self.context.lnsp_manager.lnss

    @property
    def label(self):
        """Return this app's label."""
        return self.__label

    @label.setter
    def label(self, value):
        """Set this app's label."""
        self.__label = value
        
    """ 
    Add Callbacks Below. Avaliable callbacks:
        - LoRaWAN GTW Events: 
            new_state_transition 
        - Uplink Web Socket Messages Events: 
            version, jreq, updf, propdf, dntxed, timesync, rmtsh
        - Downlink Web Socket Messages Events: 
            router_config, dnmsg, dnsched, dn_timesync, rmcmd, dn_rmtsh     
        - Monitoring Round-trip Times Events: 
            rtt_data_rx, rtt_query, rtt_on, rtt_off               
        - Gathering Radio Data Statistics Events: 
            new_radio_data 

    e.g. Callback for new Uplink Data Frame event:

    def callback_updf(self,  **kwargs):        
        lgtw_id    = kwargs.get('lgtw_id')
        # rx_time    = kwargs.get('rx_time')
        updf_data  = kwargs.get('updf_data')
        xtime      = kwargs.get('xtime')
        rctx       = kwargs.get('rctx')   
        phypayload = kwargs.get('PhyPayload')
        
        self.log.info("%s: lGTW %s, uplink frame frame received ", self.label, str(lgtw_id))
        self.log.info("%s: PhyPayload: %s ", self.label, phypayload)
        self.log.info("%s: xtime=%d, rctx=%d", self.label, xtime, rctx)
        self.log.info("%s: \n%s", self.label, json.dumps(updf_data, indent=2, sort_keys=True))
    """