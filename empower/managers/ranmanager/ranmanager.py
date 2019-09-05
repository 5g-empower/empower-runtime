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

"""Basic RAN Manager."""

from tornado.tcpserver import TCPServer

from empower.main import srv_or_die
from empower.core.service import EService

HELLO_PERIOD = 2000
HB_PERIOD = 500


class RANManager(EService):
    """Basic RAN Manager

    Base class for binary-based southbound RAN interfaces. This class must be
    extended in order to implement the protocol messages required by the
    specific RAN.

    THe only assumption this class makes is that the SBi is using TCP as
    transport protocol. Moreover all RAN devices must extend the Device base
    class and must use a 48 bits identifier (an Ethernet address).

    Parameters:
        port: the port on which the TCP server should listen (optional)
    """

    HANDLERS = []

    projects_manager = None

    def __init__(self, device_type, connection_type, proto, **kwargs):

        super().__init__(**kwargs)

        self.device_type = device_type
        self.connection_type = connection_type
        self.proto = proto
        self.devices = {}

        self.tcp_server = TCPServer()
        self.tcp_server.handle_stream = self.handle_stream

        self.connections = {}

    @property
    def port(self):
        """Return port."""

        return self.params["port"]

    @port.setter
    def port(self, value):
        """Set port."""

        if "port" in self.params and self.params["port"]:
            raise ValueError("Param port can not be changed")

        self.params["port"] = int(value)

    def start(self):
        """Start api manager."""

        super().start()

        self.projects_manager = \
            srv_or_die("empower.managers.projectsmanager.projectsmanager")

        for device in self.device_type.objects:
            self.devices[device.addr] = device

        self.tcp_server.listen(self.port)

        self.log.info("Listening on port %u", self.port)

    def handle_stream(self, stream, address):
        """Handle incoming connection."""

        self.log.info('Incoming connection from %r', address)

        connection = self.connection_type(stream, self)

        if address[0] in self.connections:
            self.log.error('Connection found from %r, closing.', address)
            self.connections[address[0]].stream.close()

        self.connections[address[0]] = connection

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = super().to_dict()
        out["connections"] = self.connections
        return out

    def create(self, addr, desc="Generic device"):
        """Create new device."""

        if addr in self.devices:
            raise ValueError("Device %s already defined" % addr)

        device = self.device_type(addr=addr, desc=desc)
        device.save()

        self.devices[device.addr] = device

        return self.devices[device.addr]

    def remove_all(self):
        """Remove all projects."""

        for addr in list(self.devices):
            self.remove(addr)

    def remove(self, addr):
        """Remove project."""

        if addr not in self.devices:
            raise KeyError("%s not registered" % addr)

        device = self.devices[addr]

        device.delete()

        del self.devices[addr]
