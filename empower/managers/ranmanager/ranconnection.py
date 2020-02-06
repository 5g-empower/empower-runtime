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

"""Base RAN Connection."""

import time
import logging

import tornado.ioloop

from empower.core.serialize import serializable_dict

HELLO_PERIOD = 2000
HB_PERIOD = 500


@serializable_dict
class RANConnection:
    """A persistent connection to a RAN device."""

    def __init__(self, stream, manager):

        self.log = logging.getLogger("%s" % self.__class__.__module__)

        self.manager = manager
        self.device = None

        self.proto = self.manager.proto

        self.stream = stream
        self.stream.set_nodelay(True)
        self.stream.set_close_callback(self.on_disconnect)

        self._seq = 0
        self._xid = 0

        self.buffer = b''

        self.xids = {}

        self.hb_worker = \
            tornado.ioloop.PeriodicCallback(self.heartbeat_cb, HB_PERIOD)

        self.wait()

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

        self._xid += 1
        return self._xid

    @property
    def seq(self):
        """Return next sequence id."""

        self._seq += 1
        return self._seq

    def wait(self):
        """ Wait for incoming packets on signalling channel """

        self.buffer = b''

        hdr_len = self.proto.HEADER.sizeof()

        future = self.stream.read_bytes(hdr_len)
        future.add_done_callback(self.on_read)

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

    def heartbeat_cb(self):
        """Check if connection is still active."""

        if self.device and not self.stream.closed():
            timeout = HELLO_PERIOD * 3
            if (self.device.last_seen_ts + (timeout / 1000)) < time.time():
                self.log.warning('Client inactive %s at %r',
                                 self.device.addr,
                                 self.stream.socket.getpeername())
                self.stream.close()

    def handle_message(self, method, msg):
        """Handle incoming message."""

        raise NotImplementedError()

    def on_read(self, future):
        """Assemble message from agent.

        Appends bytes read from socket to a buffer. Once the full packet
        has been read the parser is invoked and the buffers is cleared. The
        parsed packet is then passed to the suitable method or dropped if the
        packet type in unknown.

        The implementation of the method is southbound-specific."""

        raise NotImplementedError()

    def on_disconnect(self):
        """Handle device disconnection

        The implementation of the method is southbound-specific."""

        raise NotImplementedError()

    def send_message(self, msg_type, msg, callback=None):
        """Send message and set common parameters

        The implementation of the method is southbound-specific."""

        raise NotImplementedError()

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
