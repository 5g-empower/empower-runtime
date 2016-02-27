#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""OAIP Connection."""

import tornado.ioloop
import time

from empower.datatypes.etheraddress import EtherAddress
from empower.oaip import HEADER

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class OAIPConnection(object):
    """OAIP Connection."""

    def __init__(self, stream, addr, server):
        self.stream = stream
        self.addr = addr
        self.server = server
        self.oain = None
        self.stream.set_close_callback(self._on_disconnect)
        self.__buffer = b''
        self._hb_interval_ms = 500
        self._hb_worker = tornado.ioloop.PeriodicCallback(self._heartbeat_cb,
                                                          self._hb_interval_ms)
        self._hb_worker.start()
        self._wait()

    def to_dict(self):
        """Return dict representation of object."""

        return self.addr

    def _heartbeat_cb(self):
        """ Check if oain connection is still active. Disconnect if no hellos
        have been received from the oain for twice the hello period. """
        if self.oain and not self.stream.closed():
            timeout = (self.oain.period / 1000) * 3
            if (self.oain.last_seen_ts + timeout) < time.time():
                LOG.info('Client inactive %s at %r',
                         self.oain.addr,
                         self.addr)

                self.stream.close()

    def _on_read(self, line):
        """ Appends bytes read from socket to a buffer. Once the full packet
        has been read the parser is invoked and the buffers is cleared. The
        parsed packet is then passed to the suitable method or dropped if the
        packet type in unknown. """

        self.__buffer = self.__buffer + line
        hdr = HEADER.parse(self.__buffer)

        if len(self.__buffer) < hdr.length:
            remaining = hdr.length - len(self.__buffer)
            self.stream.read_bytes(remaining, self._on_read)
            return

        self._trigger_message(hdr.type)
        self._wait()

    def _trigger_message(self, msg_type, callback_data=None):

        if msg_type not in self.server.pt_types:

            LOG.error("Unknown message type %u", msg_type)
            return

        if self.server.pt_types[msg_type]:

            msg = self.server.pt_types[msg_type].parse(self.__buffer)
            handler_name = "_handle_%s" % self.server.pt_types[msg_type].name

            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                handler(msg)

        if msg_type in self.server.pt_types_handlers:
            for handler in self.server.pt_types_handlers[msg_type]:
                handler(msg)

    def _handle_hello(self, hello):
        """Handle an incoming HELLO message.
        Args:
            hello, a HELLO message
        Returns:
            None
        """

        oain_addr = EtherAddress(hello.oain)

        try:
            oain = RUNTIME.oains[oain_addr]
        except KeyError:
            LOG.info("Hello from unknown OAIN (%s)", (oain_addr))
            return

        LOG.info("Hello from %s seq %u", self.addr[0], hello.seq)

        # If this is a new connection, then send caps request
        if not oain.connection:
            # set oain before connection because it is used when the connection
            # attribute of the PNFDev object is set
            self.oain = oain
            oain.connection = self

        # Update OAIN params
        oain.period = hello.period
        oain.last_seen = hello.seq

        oain.last_seen_ts = time.time()

    def _wait(self):
        """ Wait for incoming packets on signalling channel """
        self.__buffer = b''
        self.stream.read_bytes(4, self._on_read)

    def _on_disconnect(self):
        """ Handle OAIN disconnection """

        if not self.oain:
            return

        LOG.info("OAIN disconnected: %s" % self.oain.addr)

        # reset state
        self.oain.last_seen = 0
        self.oain.connection = None
