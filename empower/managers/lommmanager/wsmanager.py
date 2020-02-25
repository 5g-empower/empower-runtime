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

"""Basic Web Socket (WS) Manager."""

import tornado.web

#DELETED from empower.main import srv_or_die
from empower.core.service import EService

class WSManager(EService):
    """Basic WS Manager

    Base class for text-based southbound Web Socket interface. 
    This class must be extended in order to implement the protocol 
    required by the specific device.

    The only assumption this class makes is that the SBi is using 
    Web Sockets. 
    
    Moreover all devices must extend the Device base
    class and must use a 48 bits identifier (an Ethernet address).

    Parameters:
        port: the port on which the WS server should listen (optional)
    """
    DEFAULT_PORT = 8080
    LABEL = "Generic Web Socket Server"
    DEVICE_TYPE = None
    HANDLERS = []
    WSHANDLERS = []
    ws = None
    projects_manager = None 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.devices = {}

    @property
    def port(self):
        """Return port."""
        return self.params.get("port", self.DEFAULT_PORT) 

    @port.setter
    def port(self, value):
        """Set port."""
        if "port" in self.params and self.params["port"]:
            raise ValueError("Param port can not be changed")
        self.params["port"] = int(value)

    def start(self):
        """Start control loop."""
        super().start()
            
        if self.WSHANDLERS:            
            arguments = []
            for wshandler in self.WSHANDLERS:
                arguments += wshandler.urls(dict(server=self))
            self.ws = tornado.web.Application(arguments)
            #self.ws = tornado.web.Application(arguments, debug=True)
            
            self.http_server = tornado.httpserver.HTTPServer(self.ws)
            self.http_server.listen(self.port)
            self.log.info("Listening on port %u", self.port)


        if self.DEVICE_TYPE:
            for device in self.DEVICE_TYPE.objects:
                self.devices[device.euid] = device
            
    def add(self, euid, desc="Generic device"):
        """Add new device."""
        if euid in self.devices:
            raise ValueError("Device %s already defined" % euid)

        if self.DEVICE_TYPE:
            device = self.DEVICE_TYPE(euid=euid, desc=desc)
            device.save()

            self.devices[device.euid] = device
        return self.devices.get(device.euid)

    def remove_all(self):
        """Remove all devices."""
        for euid in list(self.devices):
            self.remove(euid)

    def remove(self, euid):
        """Remove device."""

        if euid not in self.devices:
            raise KeyError("%s not registered" % euid)

        device = self.devices[euid]
        device.delete()
        del self.devices[euid]
        
    def to_dict(self):
        """Return JSON-serializable representation of the object."""
        out = super().to_dict()
        out["port"]  = self.port
        out["descr"] = self.LABEL
        if self.DEVICE_TYPE:
            out["device_type"] = DEVICE_TYPE.__name__
        return out
