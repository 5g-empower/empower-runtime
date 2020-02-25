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
"""LoMM Test App for Empower

The lomm_test application prints on screen data upon LoMM events:
    - LoRaWAN GTW Events: new_state_transition 
    - Uplink Web Socket Messages Events: version, jreq, updf, propdf, dntxed, timesync, rmtsh
    - Downlink Web Socket Messages Events: router_config, dnmsg, dnsched, dn_timesync, rmcmd, dn_rmtsh     
    - Monitoring Round-trip Times Events: rtt_data_rx, rtt_query, rtt_on, rtt_off               
    - Gathering Radio Data Statistics Events: new_radio_data 
"""

import datetime, json

import empower.managers.lommmanager.lnsp as lnsp
from   empower.core.app import EApp
from   empower.core.app import EVERY
        
__author__       = "Cristina E. Costa"
__credits__      = ["Cristina E. Costa"]
__license__      = "Apache License, Version 2.0"
__version__      = "1.0.0"
__maintainer__   = "Cristina E. Costa"
__email__        = "ccosta@fbk.eu"
__status__       = "Dev"

class LoMMTest(EApp):
    """LoMMTest App. The LoMM Test App, prints LoMM events data on screen.

    Attributes:
        context (Project): Project context in which the app is running (context.services)
        lgtws (dict): Registered LoRaWAN GTWs
        lenddevs (dict): Registered End Devices
        lnss (dict): Registered LNSs
        label (str): Application label (used in the log entries)

    Implemented callbacks:
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
    # List of empower-runtime manager/s used in the app
    MODULES  = [lnsp] 
        
    def __init__(self, **kwargs):
        """
        Parameters:
            project_id (UUID): the project id
            service_id (UUID): the app id
        """
        self.__label = None
        # Start loop
        self.startloop = True
        super().__init__(**kwargs)
        # lnsp_manager = srv_or_die("lnsp_manager")
                
    def start(self):
        """Run at app start."""
        self.log.info("%s: Registering callbacks", self.label)
        for module in self.MODULES:
            module.register_callbacks(self)         
        # start the app
        super().start()
        self.log.info("%s is up!" % self.label)

    def stop(self):
        """Run at app stop."""
        self.log.info("%s: Unegistering callbacks", self.label)
        for module in self.MODULES:
            module.unregister_callbacks(self)     
        # stop the app
        super().stop()
        
    def loop(self):
        """Periodic job."""
        pass

    @property
    def lgtws(self):
        """Return lGTWs registered in this project context."""
        # return self.context.lgtws # from project context
        return self.context.lns_manager.lgtws
        
    @property
    def lenddevs(self):
        """Return lGTWs registered in this project context."""
        # return self.context.lenddevs  # from project context
        return self.service.lns_manager.lenddevs

    @property
    def lnss(self):
        """Return LNSS registered in this project context."""
        # return self.context.lnss # from project context
        return self.context.lnsp_manager.lnss

    @property
    def label(self):
        """Return this app's label."""
        return self.__label

    @label.setter
    def label(self, value):
        """Set this app's label."""
        self.__label = value
        
    """ 
    LoRaWAN GTW Events Callback
    """
    def callback_new_state_transition(self, **kwargs):
        """Callback when a GTW changes its state
        
        Parameters:
            lgtw_id (UID): LoRaWAN GTW ID
            old_state ("disconnected", "connected", "online"): previous state of the GTW
            new_state ("disconnected", "connected", "online"): new state of the GTW
        """
        lgtw_id   = kwargs.get('lgtw_id')
        old_state = kwargs.get('old_state')
        new_state = kwargs.get('new_state')        

        self.log.info("%s: lgtw %s is %s!", self.label, lgtw_id, new_state)
        
    """ 
    Uplink Web Socket Messages Callbacks
    """
    def callback_version(self,  **kwargs):
        """Callback when a new Version message arrives """           
        lgtw_id      = kwargs.get('lgtw_id')
        rx_time      = kwargs.get('rx_time')
        lgtw_version = kwargs.get('lgtw_version')
        
        self.log.info("%s: lGTW %s, version request received ", self.label, str(lgtw_id))
        self.log.info("%s: \n%s", self.label, json.dumps(lgtw_version))
        
    def callback_jreq(self,  **kwargs):
        """Callback when a new JREQ Frame arrives """           
        lgtw_id    = kwargs.get('lgtw_id')
        rx_time    = kwargs.get('rx_time')
        join_data  = kwargs.get('join_data')
        xtime      = kwargs.get('xtime')
        rctx       = kwargs.get('rctx')        
        phypayload = kwargs.get('PhyPayload')
        
        self.log.info("%s: lGTW %s, join request frame received ", self.label, str(lgtw_id))
        self.log.info("%s: PhyPayload: %s ", self.label, phypayload)
        self.log.info("%s: xtime=%d, rctx=%d", self.label, xtime, rctx)
        self.log.info("%s: \n%s", self.label, json.dumps(join_data, indent=2, sort_keys=True))
        
    def callback_updf(self,  **kwargs):
        """Callback when a new Uplink Data Frame arrives """           
        lgtw_id    = kwargs.get('lgtw_id')
        rx_time    = kwargs.get('rx_time')
        updf_data  = kwargs.get('updf_data')
        xtime      = kwargs.get('xtime')
        rctx       = kwargs.get('rctx')   
        phypayload = kwargs.get('PhyPayload')
        
        self.log.info("%s: lGTW %s, uplink frame frame received ", self.label, str(lgtw_id))
        self.log.info("%s: PhyPayload: %s ", self.label, phypayload)
        self.log.info("%s: xtime=%d, rctx=%d", self.label, xtime, rctx)
        self.log.info("%s: \n%s", self.label, json.dumps(updf_data, indent=2, sort_keys=True))
        
    def callback_propdf(self,  **kwargs):
        """Callback when a new Proprietary Frame arrives """           
        lgtw_id    = kwargs.get('lgtw_id')
        rx_time    = kwargs.get('rx_time')
        frmpayload = kwargs.get('FRMPayload')
        xtime      = kwargs.get('xtime')
        rctx       = kwargs.get('rctx')
        
        self.log.info("%s: lGTW %s, proprietary frame received ", self.label, str(lgtw_id))
        self.log.info("%s: xtime=%d, rctx=%d", self.label, self.label, xtime, rctx)
        self.log.info("%s: frmpayload=%s", self.label, frmpayload)
        
    def callback_dntxed(self, **kwargs):
        """Callback when a new Transmit Confirmation message arrives """ 
        """
        This message is only sent when a frame has been put on air. 
        There is no feedback to the LNS if a frame could not be sent
        """           
        lgtw_id    = kwargs.get('lgtw_id')
        rx_time    = kwargs.get('rx_time')
        dntxed     = kwargs.get('dntxed')
        
        self.log.info("%s: lGTW %s, packet transmission confirmation received ", self.label, str(lgtw_id))
        self.log.info("%s: xtime=%d, rctx=%d", self.label, dntxed['xtime'], dntxed['rctx'])
        self.log.info("%s: \n%s", self.label, json.dumps(dntxed, indent=2, sort_keys=True))
        
    def callback_timesync(self,  **kwargs):
        """Callback when a new Timesync message arrives """           
        lgtw_id    = kwargs.get('lgtw_id')
        rx_time    = kwargs.get('rx_time')
        
        if 'gpstime' in kwargs:
            self.log.info("%s: lGTW %s, Transferring GPS Time (timesync) message received (gpstime=%d, xtime=%d)", self.label, str(lgtw_id), kwargs['gpstime'], kwargs['xtime'])
        else:
            self.log.info("%s: lGTW %s, GPS Time syncronization (timesync) message received (txtime=%d)", self.label, str(lgtw_id), kwargs['txtime'])
        
    def callback_rmtsh(self,  **kwargs):
        """Callback when a new remote shell message arrives """           
        lgtw_id      = kwargs.get('lgtw_id')
        rx_time      = kwargs.get('rx_time')
        rmtsh        = kwargs.get('rmtsh')
        
        self.log.info("%s: lGTW %s, current remote shell sessions state received ", self.label, str(lgtw_id))
        
        for session in rmtsh:
            if rmtsh['started']:
              self.log.info("%s: session pid = %d (running), user %s, %d secs since the input/output action", self.label, str(lgtw_id), 
                            rmtsh['pid'], rmtsh['user'], rmtsh['age'])
            else:
              self.log.info("%s: session pid = %d, user %s, %d secs since the input/output action", self.label, str(lgtw_id), 
                            rmtsh['pid'], rmtsh['user'], rmtsh['age'])


    """ 
    Downlink Web Socket Messages
    """      
    def callback_router_config(self,  **kwargs):
        """Callback when a new remote shell message is sent """          
        lgtw_id       = kwargs.get('lgtw_id')
        tx_time       = kwargs.get('tx_time')
        router_config = kwargs.get('msg')
        
        self.log.info("%s: lGTW %s, lGTW configuration sent.", self.label, str(lgtw_id))
        self.log.info("%s: \n%s", self.label, json.dumps(router_config, indent=2, sort_keys=True))
        
    def callback_dnmsg(self,  **kwargs):
        """Callback when a new downlink frame message is sent """          
        lgtw_id       = kwargs.get('lgtw_id')
        tx_time       = kwargs.get('tx_time')
        dnmsg         = kwargs.get('msg')
        
        self.log.info("%s: lGTW %s, new frame sent for transmission.", self.label, str(lgtw_id))
        ##TODO CHECK
        if dnmsg:
            self.log.info("%s: xtime=%d, rctx=%d", self.label, dnmsg['xtime'], dnmsg['rctx'])
            self.log.info("%s: \n%s", self.label, json.dumps(dnmsg, indent=2, sort_keys=True))
        
    def callback_dnsched(self,  **kwargs):
        """Callback when a new downlink scheduled frame message is sent """          
        lgtw_id       = kwargs.get('lgtw_id')
        tx_time       = kwargs.get('tx_time')
        dnsched       = kwargs.get('msg')
        
        self.log.info("%s: lGTW %s, new frames scheduled for transmission.", self.label, str(lgtw_id))
        for frame in dnsched:
            if "rctx" in dnsched:
                self.log.info("%s: DR=%d, Freq=%d, priority=%d, gpstime=%d, rctx=%d", self.label, dnsched['DR'], dnsched['Freq'], dnsched['priority'], dnsched['gpstime'], dnsched['rctx'] )
            else:
                self.log.info("%s: DR=%d, Freq=%d, priority=%d, gpstime=%d", self.label, dnsched['DR'], dnsched['Freq'], dnsched['priority'], dnsched['gpstime'] )
            self.log.info("%s: pdu=%s", self.label, dnsched['pdu'])
      
    def callback_dn_timesync(self,  **kwargs):
        """Callback when a new timesync message is sent """           
        lgtw_id       = kwargs.get('lgtw_id')
        tx_time       = kwargs.get('tx_time')
        timesync      = kwargs.get('msg')
        
        self.log.info("%s: lGTW %s, timesync message (txtime=%d) sent to lGTW, gpstime=%d microsecs since GPS epoch ", self.label, str(lgtw_id), timesync['txtime'], timesync['gpstime'])
  
    def callback_rmcmd(self,  **kwargs):
        """Callback when a new remote command message is sent """           
        lgtw_id       = kwargs.get('lgtw_id')
        tx_time       = kwargs.get('tx_time')
        rmcmd         = kwargs.get('msg')
        args = ""
        for arg in rmcmd['arguments']:
            args += arg + " "
        self.log.info("%s: lGTW %s, remote command sent to lGTW > %s %s ", self.label, str(lgtw_id), rmcmd['command'], args) 
        
    def callback_dn_rmtsh(self,  **kwargs):
        """Callback when a new remote shell message is sent """           
        lgtw_id       = kwargs.get('lgtw_id')
        tx_time       = kwargs.get('tx_time')
        rmtsh         = kwargs.get('msg')
        user          = rmtsh.get('user')
        term          = rmtsh.get('term')  
         
        if 'start' in rmtsh:
            self.log.info("%s: lGTW %s, remote shell session start, user %s, term %s ", self.label, str(lgtw_id), user, term)  
        elif 'stop' in rmtsh:
            self.log.info("%s: lGTW %s, remote shell session stop, user %s, term %s ", self.label, str(lgtw_id), user, term)  
        else: 
            self.log.info("%s: lGTW %s, current remote shell session state query sent, user %s, term %s ", self.label, str(lgtw_id), user, term)  
        
    """ 
    Monitoring Round-trip Times
    """      
    def callback_rtt_data_rx(self, **kwargs):
        """Callback when new RTT data is avaliable"""
        """
        The field RefTime is calculated from the last received MuxTime adjusted 
        by the time interval on the router between the arrival of MuxTime and the sending of RefTime. 
        Since downlink traffic is less frequent than uplink messages, 
        it is likely that a MuxTime is reused to construct multiple RefTime fields. 
        This means that round-trip measurements are composed of the latency of the last 
        downlink message and the most recent uplink message.
        """
        lgtw_id   = kwargs.get('lgtw_id')
        RefTime   = kwargs.get('RefTime')  
        self.log.info("%s: lGTW %s, new RTT data arrived, RefTime = %f", self.label, str(lgtw_id), RefTime)    
            
     
    def callback_rtt_query(self, **kwargs):
        """ Callback new RTT query is sent """
        lgtw_id   = kwargs.get('lgtw_id')
        MuxTime   = kwargs.get('MuxTime')  
        """
        The field MuxTime contains a float value representing a UTC timestamp 
        with fractional seconds and marks the time when this message was sent by the LNS. 
        """
        self.log.info("%s: lGTW %s, new RTT data sent%s", self.label, str(lgtw_id),  ", MuxTime = %f" % 0.0 if isinstance(MuxTime, float) else "")
        
    def callback_rtt_on(self, **kwargs):
        """ Callback RTT query is set to ON """
        lgtw_id   = kwargs.get('lgtw_id')
        self.log.info("%s: lGTW %s, RTT set to ON.", self.label, str(lgtw_id))
        
    def callback_rtt_off(self, **kwargs):
        """ Callback RTT query is set to OFF """
        lgtw_id   = kwargs.get('lgtw_id')
        self.log.info("%s: lGTW %s, RTT set to OFF.", self.label, str(lgtw_id))
                
    """ 
    Gathering Radio Data statistics
    """         
    def callback_new_radio_data(self, **kwargs):
        """Callback when a LoRaWAN Radio GTW radio data is avaliable"""
        lgtw_id    = kwargs.get('lgtw_id')
        radio_data = kwargs.get('radio_data')  
        dev_eui    = kwargs.get('DevEui')
        dev_addr   = kwargs.get('DevAddr')
        rxtime     = kwargs.get('rxtime')
        
        self.log.info("%s: lGTW %s, New Radio Data.", self.label, str(lgtw_id))
        self.log.info("%s: \n%s", self.label, json.dumps(radio_data, indent=2, sort_keys=True))

def launch(context, service_id, label="LoMM Test App"):
    """Initialize the module."""
    return LoMMTest(context=context, service_id=service_id, label=label)