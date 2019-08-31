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

"""RAN Connection."""

import time
import logging

import tornado.ioloop

from tornado.iostream import StreamClosedError
from construct import Container

from empower.core.etheraddress import EtherAddress

HELLO_PERIOD = 2000
HB_PERIOD = 500


class RANConnection:
    """A persistent connection to a RAN device."""

    def __init__(self, stream, manager):

        self.log = logging.getLogger("%s" % self.__class__.__module__)

        self.manager = manager
        self.device = None

        self.proto = self.manager.proto

        self.stream = stream
        self.stream.set_nodelay(True)
        self.stream.set_close_callback(self._on_disconnect)

        self.__seq = 0

        self.__buffer = b''

        self.__xid = 0

        self.__xids = {}

        self._hb_worker = \
            tornado.ioloop.PeriodicCallback(self._heartbeat_cb, HB_PERIOD)

        self._hello_worker = \
            tornado.ioloop.PeriodicCallback(self._hello_cb, HELLO_PERIOD)

        self.send_hello_request()

        self._wait()

    def to_dict(self):
        """Return dict representation of object."""

        out = {
            "proto": self.proto.__name__,
            "addr": None
        }

        if self.stream and self.stream.socket:
            addr = self.stream.socket.getpeername()
            out['addr'] = addr[0]

        return out

    @property
    def xid(self):
        """Return new xid."""

        self.__xid += 1
        return self.__xid

    @property
    def seq(self):
        """Return next sequence id."""

        self.__seq += 1
        return self.__seq

    def _wait(self):
        """ Wait for incoming packets on signalling channel """

        self.__buffer = b''

        hdr_len = self.proto.HEADER.sizeof()

        future = self.stream.read_bytes(hdr_len)
        future.add_done_callback(self._on_read)

    def send_message_to_self(self, target, pt_type):
        """Send a message to self."""

        if pt_type in self.proto.PT_TYPES_HANDLERS:
            for handler in self.proto.PT_TYPES_HANDLERS[pt_type]:
                handler(target)

    def send_client_leave_message_to_self(self, client):
        """Send an CLIENT_LEAVE message to self."""

        self.send_message_to_self(client, self.proto.PT_CLIENT_LEAVE)

    def send_client_join_message_to_self(self, client):
        """Send an CLIENT_JOIN message to self."""

        self.send_message_to_self(client, self.proto.PT_CLIENT_JOIN)

    def send_device_up_message_to_self(self):
        """Send a unsollicited DEVICE_UP message to self."""

        self.send_message_to_self(self.device, self.proto.PT_DEVICE_UP)

    def send_device_down_message_to_self(self):
        """Send a unsollicited DEVICE_DOWN message to self."""

        self.send_message_to_self(self.device, self.proto.PT_DEVICE_DOWN)

    def _hello_cb(self):
        """Send periodic hello request."""

        self.send_hello_request()

    def _heartbeat_cb(self):
        """Check if connection is still active."""

        if self.device and not self.stream.closed():
            timeout = HELLO_PERIOD * 3
            if (self.device.last_seen_ts + timeout) < time.time():
                self.log.warning('Client inactive %s at %r',
                                 self.device.addr,
                                 self.stream.socket.getpeername())
                self.stream.close()

    def _on_read(self, future):
        """Appends bytes read from socket to a buffer. Once the full packet
        has been read the parser is invoked and the buffers is cleared. The
        parsed packet is then passed to the suitable method or dropped if the
        packet type in unknown."""

        try:
            self.__buffer = self.__buffer + future.result()
        except StreamClosedError as stream_ex:
            self.log.error(stream_ex)
            return

        hdr = self.proto.HEADER.parse(self.__buffer)

        if len(self.__buffer) < hdr.length:
            remaining = hdr.length - len(self.__buffer)
            future = self.stream.read_bytes(remaining)
            future.add_done_callback(self._on_read)
            return

        # Check if we know the message type
        if hdr.type not in self.proto.PT_TYPES:
            self.log.warning("Unknown message type %u, ignoring.", hdr.type)
            return

        # Check if the Device is among the ones we known
        addr = EtherAddress(hdr.device)

        if addr not in self.manager.devices:
            self.log.warning("Unknown Device %s, closing connection.", addr)
            self.stream.close()
            return

        device = self.manager.devices[addr]

        # Log message informations
        parser = self.proto.PT_TYPES[hdr.type]
        msg = parser.parse(self.__buffer)
        self.log.debug("Got %s message from %s seq %u", parser.name,
                       EtherAddress(addr), hdr.seq)

        # If Device is not online and is not connected, then the only message
        # type we can accept is HELLO_RESPONSE
        if not device.is_connected():

            if msg.type != self.proto.PT_HELLO_RESPONSE:
                if not self.stream.closed():
                    self._wait()
                return

            # This is a new connection, set pointer to the device
            self.device = device

            # The set pointer from device connection to this object
            device.connection = self

            # Transition to connected state
            device.set_connected()

            # Start hello and hb workers
            self._hb_worker.start()
            self._hello_worker.start()

            # Send caps request
            self.send_caps_request()

        # If device is not online but it is connected, then we can accept both
        # HELLO_RESPONSE and CAP_RESPONSE message
        if device.is_connected() and not device.is_online():
            valid = (self.proto.PT_HELLO_RESPONSE, self.proto.PT_CAPS_RESPONSE)
            if msg.type not in valid:
                if not self.stream.closed():
                    self._wait()
                return

        # Otherwise handle message
        try:
            self._handle_message(device, msg)
        except Exception as ex:
            self.log.exception(ex)
            self.stream.close()

        if not self.stream.closed():
            self._wait()

    def _handle_message(self, device, msg):
        """Handle incoming message."""

        # If the default handler is defined then call it
        handler_name = "_handle_%s" % self.proto.PT_TYPES[msg.type].name
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            handler(msg)

        # Call registered callbacks
        if msg.type in self.proto.PT_TYPES_HANDLERS:
            for handler in self.proto.PT_TYPES_HANDLERS[msg.type]:
                handler(msg, device)

        # Check if there are pending XIDs
        if msg.xid in self.__xids:
            request = self.__xids[msg.xid][0]
            callback = self.__xids[msg.xid][1]
            if callback:
                callback(msg, device, request)
            del self.__xids[msg.xid]

    def _wait(self):
        """ Wait for incoming packets on signalling channel """

        self.__buffer = b''

        hdr_len = self.proto.HEADER.sizeof()

        future = self.stream.read_bytes(hdr_len)
        future.add_done_callback(self._on_read)

    def _on_disconnect(self):
        """ Handle device disconnection """

        if not self.device:
            return

        self.log.warning("Device disconnected: %s", self.device.addr)

        # perform clean ups.
        self.on_disconnect()

        # reset state
        self.device.set_disconnected()
        self.device.last_seen = 0
        self.device.connection = None
        self.device.blocks = {}
        self.device = None

        # Stop hello and hb workers
        self._hb_worker.stop()
        self._hello_worker.stop()

    def on_disconnect(self):
        """Handle protocol-specific device disconnection."""

    def send_message(self, msg_type, msg, callback=None):
        """Send message and set common parameters."""

        parser = self.proto.PT_TYPES[msg_type]

        if self.stream.closed():
            self.log.warning("Stream closed, unabled to send %s message to %s",
                             parser.name, self.device)
            return 0

        msg.version = self.proto.PT_VERSION
        msg.seq = self.seq
        msg.type = msg_type
        msg.xid = self.xid

        if not self.device:
            msg.device = EtherAddress("00:00:00:00:00:00").to_raw()
        else:
            msg.device = self.device.addr.to_raw()

        addr = self.stream.socket.getpeername()

        self.log.debug("Sending %s message to %s seq %u",
                       parser.name, addr[0], msg.seq)

        self.stream.write(parser.build(msg))

        if callback:
            self.__xids[msg.xid] = (msg, callback)

        return msg.xid

    def _handle_hello_response(self, hello):
        """Handle an incoming HELLO_RESPONSE message."""

        self.device.last_seen = hello.seq
        self.device.last_seen_ts = time.time()

    def _handle_caps_response(self, _):
        """Handle an incoming CAPS message."""

        # set state to online
        self.device.set_online()

    def send_hello_request(self):
        """Send a HELLO_REQUEST message."""

        msg = Container(length=self.proto.HELLO_REQUEST.sizeof())
        return self.send_message(self.proto.PT_HELLO_REQUEST, msg)

    def send_caps_request(self):
        """Send a CAPS_REQUEST message."""

        msg = Container(length=self.proto.CAPS_REQUEST.sizeof())
        return self.send_message(self.proto.PT_CAPS_REQUEST, msg)

    def to_str(self):
        """Return representation of the project."""

        if self.stream and self.stream.socket:
            return "%s:%u" % self.stream.socket.getpeername()

        return None

    def __str__(self):
        return self.to_str()

    def __eq__(self, other):
        if isinstance(other, RANConnection):
            return self.stream == other.stream
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
