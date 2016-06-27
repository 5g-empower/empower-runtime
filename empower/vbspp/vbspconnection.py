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

"""VBSP Connection."""

import time
import tornado.ioloop
from construct import Container

import empower.vbspp.messages.progran_pb2 as progran_pb2
import empower.vbspp.messages.header_pb2 as header_pb2
from empower.datatypes.etheraddress import EtherAddress
from empower.vbspp import MESSAGE_SIZE
from empower.vbspp import PRT_VBSP_BYE
from empower.vbspp import PRT_VBSP_REGISTER
from empower.vbspp import PROGRAN_VERSION

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class VBSPConnection(object):
    """VBSP Connection.

    Represents a connection to a ENB (EUTRAN Base Station) using
    the VBSP Protocol. One VBSPConnection object is created for every
    ENB in the network. The object implements the logic for handling
    incoming messages. The currently supported messages are:

    Attributes:
        stream: The stream object used to talk with the ENB.
        address: The connection source address, i.e. the ENB IP address.
        server: Pointer to the server object.
        vbsp: Pointer to a VBSP object.
    """

    def __init__(self, stream, addr, server):
        self.stream = stream
        self.addr = addr
        self.server = server
        self.vbsp = None
        self.enb_id = None
        self.vbsp_id = None
        self.stream.set_close_callback(self._on_disconnect)
        self._hb_interval_ms = 500
        self._hb_worker = tornado.ioloop.PeriodicCallback(self._heartbeat_cb,
                                                          self._hb_interval_ms)
        self._hb_worker.start()
        self._wait()

    def to_dict(self):
        """Return dict representation of object."""

        return self.addr

    def _heartbeat_cb(self):
        """ Check if wtp connection is still active. Disconnect if no hellos
        have been received from the wtp for twice the hello period. """
        if self.vbsp and not self.stream.closed():
            timeout = (self.vbsp.period / 1000) * 3
            if (self.vbsp.last_seen_ts + timeout) < time.time():
                LOG.info('Client inactive %s at %r', self.vbsp.addr, self.addr)
                self.stream.close()

    def create_header(self, xid, eid, message_type, header):

        if not header:
            LOG.error("header parameter is None")

        header.version = PROGRAN_VERSION
        header.type = message_type
        header.xid = xid
        header.eid = eid

    def build_size_message(self, size):

        size_message = Container(length=size)
        return MESSAGE_SIZE.build(size_message)

    def serialize_message(self, message):

        if not message:
            LOG.error("message parameter is None")
            return None

        return message.SerializeToString()

    def deserialize_message(self, serialized_data):

        if not serialized_data:
            LOG.error("Received serialized data is None")
            return None

        msg = progran_pb2.progran_message()
        msg.ParseFromString(serialized_data)

        return msg

    def stream_send(self, message):

        err_code = progran_pb2.NO_ERR

        size = message.ByteSize()
        send_buff = self.serialize_message(message)
        size_message = self.build_size_message(size)

        if send_buff is None:
            err_code = progran_pb2.MSG_ENCODING
            LOG.error("errno %u occured", err_code)

        # First send the length of the message and then the actual message
        self.stream.write(size_message)
        self.stream.write(send_buff)

    def send_echo_request(self, enb_id, xid=0):

        echo_request = progran_pb2.progran_message()

        self.create_header(xid, enb_id, header_pb2.PRPT_ECHO_REQUEST,
                           echo_request.echo_request_msg.header)
        echo_request.msg_dir = progran_pb2.INITIATING_MESSAGE

        LOG.info("Sending echo request message to VBSP %f", self.vbsp.addr)
        self.stream_send(echo_request)

    def _handle_echo_request(self, enb_id, echo_request):

        if echo_request is None:
            LOG.error("Echo request message is null")

        xid = echo_request.echo_request_msg.header.xid

        echo_reply = progran_pb2.progran_message()

        self.create_header(xid, enb_id, header_pb2.PRPT_ECHO_REPLY,
                           echo_reply.echo_reply_msg.header)

        echo_reply.msg_dir = progran_pb2.SUCCESSFUL_OUTCOME

        LOG.info("Sending echo reply message to VBSP %f", self.vbsp.addr)
        self.stream_send(echo_reply)

    def _on_read(self, line):
        """ Appends bytes read from socket to a buffer. Once the full packet
        has been read the parser is invoked and the buffers is cleared. The
        parsed packet is then passed to the suitable method or dropped if the
        packet type in unknown. """

        if line is not None:

            # Checking for size message (4 Bytes)
            if len(line) == 4:
                size = MESSAGE_SIZE.parse(line)
                remaining = size.length
                self.stream.read_bytes(remaining, self._on_read)
                return

            deserialized_msg = self.deserialize_message(line)

            self._trigger_message(deserialized_msg)
            self._wait()

    def _trigger_message(self, deserialized_msg):

        msg_type = deserialized_msg.WhichOneof("msg")

        if not msg_type or msg_type not in self.server.pt_types:

            LOG.error("Unknown message type %u", msg_type)
            return

        handler_name = "_handle_%s" % self.server.pt_types[msg_type]

        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            handler(deserialized_msg)

        if msg_type in self.server.pt_types_handlers:
            for handler in self.server.pt_types_handlers[msg_type]:
                handler(deserialized_msg)

    def hex_enb_id_to_ether_address(self, enb_id):

        str_hex_value = format(enb_id, 'x')
        padding = '0' * (12 - len(str_hex_value))
        mac_string = padding + str_hex_value
        mac_string_array = \
            [mac_string[i:i+2] for i in range(0, len(mac_string), 2)]

        return EtherAddress(":".join(mac_string_array))

    def _handle_hello(self, hello):
        """Handle an incoming HELLO message.
        Args:
            hello, a HELLO message
        Returns:
            None
        """

        if not self.enb_id:
            self.enb_id = hello.hello_msg.header.eid
            self.vbsp_id = self.hex_enb_id_to_ether_address(self.enb_id)
        elif self.enb_id != hello.hello_msg.header.eid:
            LOG.error("Hello from different eNB (%f)",
                      hello.hello_msg.header.eid)
            return

        try:
            vbsp = RUNTIME.vbsps[self.vbsp_id]
        except KeyError:
            LOG.error("Hello from unknown VBSP (%s)", (self.vbsp_id))
            return

        LOG.info("Hello from %s, VBSP %s", self.addr[0], self.vbsp_id.to_str())

        # If this is a new connection, then send enb status request or enb
        # config request
        if not vbsp.connection:
            # set enb before connection because it is used when the connection
            # attribute of the PNFDev object is set
            self.vbsp = vbsp
            vbsp.connection = self
            vbsp.period = 5000
            # self.send_caps_request()

        # Update VBSP params
        # vbsp.period = 5000000
        # wtp.last_seen = hello.seq
        vbsp.last_seen_ts = time.time()

    def _wait(self):
        """ Wait for incoming packets on signalling channel """
        self.stream.read_bytes(4, self._on_read)

    def _on_disconnect(self):
        """Handle VBSP disconnection."""

        if not self.vbsp:
            return

        LOG.info("VBSP disconnected: %s", self.vbsp.addr)

        # reset state
        self.vbsp.last_seen = 0
        self.vbsp.connection = None

        # remove hosted LVAPs
        to_be_removed = []
        for vbsp in RUNTIME.vbsps.values():
            if vbsp == self.vbsp:
                to_be_removed.append(vbsp)

    def send_bye_message_to_self(self):
        """Send a unsollicited BYE message to self."""

        for handler in self.server.pt_types_handlers[PRT_VBSP_BYE]:
            handler(self.vbsp)

    def send_register_message_to_self(self):
        """Send a REGISTER message to self."""

        for handler in self.server.pt_types_handlers[PRT_VBSP_REGISTER]:
            handler(self.vbsp)
