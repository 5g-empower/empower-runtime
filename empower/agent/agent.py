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

"""The EmPOWER Agent."""

import re
import sys
import json
import websocket
import _thread
import time

from uuid import UUID
from argparse import ArgumentParser

from empower.datatypes.etheraddress import EtherAddress
from empower.core.jsonserializer import EmpowerEncoder
from empower.agent.lvnf import get_hw_addr
from empower.agent.lvnf import exec_cmd
from empower.agent.lvnf import LVNF
from empower.lvnfp import PT_VERSION
from empower.lvnfp import PT_HELLO
from empower.lvnfp import PT_CAPS_RESPONSE
from empower.lvnfp import PT_STATUS_LVNF
from empower.lvnf_stats import PT_LVNF_STATS_RESPONSE
from empower.handlers import PT_READ_HANDLER_RESPONSE
from empower.handlers import PT_WRITE_HANDLER_RESPONSE
from empower.core.image import Image

BRIDGE = "br0"
DEFAULT_EVERY = 2
CTRL_IP = "127.0.0.1"
CTRL_PORT = 4422
CLICK_LISTEN = 7000
OF_CTRL = None


def on_open(ws):
    """ Called when the web-socket is opened. """

    print("Socket opened...")

    def run(ws):
        if ws.sock and ws.sock.connected:
            ws.send_hello()
            time.sleep(ws.every)
            _thread.start_new_thread(run, (ws,))

    _thread.start_new_thread(run, (ws,))


def on_message(ws, message):
    """ Called on receiving a new message. """

    try:
        ws.downlink_bytes += len(message)
        msg = json.loads(message)
        ws._handle_message(msg)
    except ValueError:
        print("Invalid input: %s", message)


def on_close(ws):
    """ Called when the web-socket is closed. """

    print("Socket closed...")


class EmpowerAgent(websocket.WebSocketApp):
    """The Empower Agent.

    Attributes:
        bridge: The OpenVSwitch bridge used by this agent
        addr: This agent id (EtherAddress)
        seq: The next sequence number (int)
        prefix: The next virtual network function interface prefix (int)
        every: The hello period (in s)
        functions: the currently deployed lvnfs
        vnf_seq: the next virtual tap interface id
    """

    def __init__(self, url, ctrl, bridge, every, listen):

        super().__init__(url)

        self.__bridge = None
        self.__ctrl = None
        self.__seq = 0
        self.__prefix = 0
        self.__vnf_seq = 0
        self.addr = None
        self.every = every
        self.listen = listen
        self.functions = {}
        self.lvnfs = {}
        self.downlink_bytes = 0
        self.uplink_bytes = 0
        self.bridge = bridge
        self.ctrl = ctrl

        print("Initializing the EmPOWER Agent...")
        print("Bridge %s (hwaddr=%s)" % (self.bridge, self.addr))

        for port in self.ports.values():
            print("Port %u (iface=%s, hwaddr=%s)" % (port['port_id'],
                                                     port['iface'],
                                                     port['hwaddr']))

    def shutdown(self):
        """Gracefully stop agent."""

        for lvnf in self.lvnfs.values():
            lvnf.stop()

    @property
    def ports(self):
        """Return the ports on the bridge.

        Fetch the list of ports currently defined on the OVS switch.

        Returns:
            A dict mapping port id with interface name and hardware address.
            For example:

            {1: {'iface': 'eth0', 'addr': EtherAddress('11:22:33:44:55:66')}}

        Raises:
            OSError: An error occured accessing the interface.
            FileNotFoundError: an OVS utility is not available.
        """

        ports = {}

        if not self.bridge:
            raise OSError('Bridge is not defined')

        cmd = ["ovs-ofctl", "show", self.bridge]
        lines = exec_cmd(cmd).split('\n')

        for line in lines:
            regexp = '([0-9]*)\((.*)\): addr:([0-9a-fA-F:]*)'
            m = re.match(regexp, line.strip())
            if m:
                groups = m.groups()
                ports[int(groups[0])] = {'port_id': int(groups[0]),
                                         'iface': groups[1],
                                         'hwaddr': EtherAddress(groups[2])}

        return ports

    @property
    def bridge(self):
        """Return the bridge."""

        return self.__bridge

    @bridge.setter
    def bridge(self, bridge):
        """Set the bridge.

        Set the bridge for this agent. The method checks if a bridge with the
        specified name exists and then tries to fetch the list of ports on
        this switch.

        Args:
            bridge: The name of the bridge as a string.

        Returns:
            None

        Raise:
            OSError: An error occured accessing the interface.
            FileNotFoundError: an OVS utility is not available.
        """

        self.addr = EtherAddress(get_hw_addr(bridge))
        self.__bridge = bridge

        if not self.ports:
            print("Warning, no ports available on bridge %s" % self.bridge)

        cmd = ["ovs-vsctl", "list-ports", self.bridge]
        lines = exec_cmd(cmd).split('\n')

        for line in lines:
            regexp = 'vnf-([A-Za-z0-9]*)-([0-9]*)-([0-9]*)'
            match = re.match(regexp, line.strip())
            if match:
                groups = match.groups()
                iface = "vnf-%s-%s-%s" % groups
                print("Stale port found %s" % iface)
                exec_cmd(["ovs-vsctl", "del-port", self.bridge, iface])

    @property
    def ctrl(self):
        """Return the ctrl."""

        return self.__ctrl

    @ctrl.setter
    def ctrl(self, ctrl):
        """Set the ctrl.

        Set the controller for the bridge used by this agent. This must be
        called AFTER setting the bridge otherwise the method will fail.

        Args:
            ctrl: the controller url in the for tcp:<ip>:<port>

        Returns:
            None

        Raise:
            OSError: An error occured accessing the interface.
            FileNotFoundError: an OVS utility is not available.
        """

        if not ctrl:
            self.__ctrl = None
            return

        cmd = ["ovs-vsctl", "set-controller", self.bridge, ctrl]
        exec_cmd(cmd)

        self.__ctrl = ctrl

    @property
    def seq(self):
        """Return the next sequence number."""

        self.__seq += 1
        return self.__seq

    def prefix(self):
        """Return the next virtual network function interface prefix."""

        self.prefix += 1
        return self.prefix

    def _handle_message(self, msg):
        """ Handle incoming message (as a Python dict). """

        handler_name = "_handle_%s" % msg['type']

        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            try:
                handler(msg)
            except Exception as ex:
                print(ex)
        else:
            print("Unknown message type: %s" % msg['type'])

    def dump_message(self, message):
        """Dump a generic message.

        Args:
            message, a message

        Returns:
            None
        """

        header = "Received %s seq %u" % (message['type'], message['seq'])

        del message['version']
        del message['type']
        del message['seq']

        fields = ["%s=%s" % (k, v)for k, v in message.items()]
        print("%s (%s)" % (header, ", ".join(fields)))

    def _handle_error(self, error):
        """Handle ERROR message.

        Args:
            error, a ERROR message

        Returns:
            None
        """

        self.dump_message(error)

    def _handle_caps_request(self, caps_request):
        """Handle CAPS_REQUEST message.

        Args:
            message, a CAPS_REQUEST message
        Returns:
            None
        """

        self.dump_message(caps_request)
        self.send_caps_response()

    def send_message(self, message_type, message):
        """Add fixed header fields and send message. """

        message['version'] = PT_VERSION
        message['type'] = message_type
        message['addr'] = self.addr
        message['seq'] = self.seq
        message['every'] = self.every

        print("Sending %s seq %u" % (message['type'], message['seq']))
        msg = json.dumps(message, cls=EmpowerEncoder)
        self.uplink_bytes += len(msg)
        self.send(json.dumps(message, cls=EmpowerEncoder))

    def send_hello(self):
        """ Send HELLO message. """

        hello = {'uplink_bytes': self.uplink_bytes,
                 'downlink_bytes': self.downlink_bytes}

        self.send_message(PT_HELLO, hello)

    def send_caps_response(self, lvnf_id=None):
        """ Send CAPS RESPONSE message. """

        caps = {'ports': self.ports}
        self.send_message(PT_CAPS_RESPONSE, caps)

        # send lvnf status message
        if not lvnf_id:
            for lvnf_id in self.lvnfs:
                self.send_status_lvnf(lvnf_id)
        else:
            self.send_status_lvnf(lvnf_id)

    @property
    def vnf_seq(self):
        """Return new VNF seq."""

        self.__vnf_seq += 1
        return self.__vnf_seq

    def _handle_lvnf_stats_request(self, message):
        """Handle LVNF_STATS message.

        Args:
            message, a LVNF_STATS message
        Returns:
            None
        """

        self.dump_message(message)

        lvnf_id = UUID(message['lvnf_id'])

        if lvnf_id not in self.lvnfs:
            raise KeyError("LVNF %s not found" % lvnf_id)

        message['stats'] = self.lvnfs[lvnf_id].stats()

        self.send_message(PT_LVNF_STATS_RESPONSE, message)

    def _handle_add_lvnf(self, message):
        """Handle ADD_LVNF message.

        Args:
            message, a ADD_LVNF message
        Returns:
            None
        """

        self.dump_message(message)

        lvnf_id = UUID(message['lvnf_id'])
        tenant_id = UUID(message['tenant_id'])

        if lvnf_id in self.lvnfs:

            print("LVNF %s found, removing." % lvnf_id)

            lvnf = self.lvnfs[lvnf_id]
            lvnf.stop()

            del self.lvnfs[lvnf_id]

        image = Image(nb_ports=message['image']['nb_ports'],
                      vnf=message['image']['vnf'],
                      state_handlers=message['image']['state_handlers'],
                      handlers=message['image']['handlers'],)

        lvnf = LVNF(agent=self,
                    lvnf_id=lvnf_id,
                    tenant_id=tenant_id,
                    image=image,
                    bridge=self.bridge,
                    vnf_seq=self.vnf_seq)

        lvnf.start()
        self.lvnfs[lvnf_id] = lvnf

    def _handle_del_lvnf(self, message):
        """Handle DEL_LVNF message.

        Args:
            message, a DEL_LVNF message
        Returns:
            None
        """

        self.dump_message(message)

        lvnf_id = UUID(message['lvnf_id'])

        if lvnf_id not in self.lvnfs:
            raise KeyError("LVNF %s not found" % lvnf_id)

        lvnf = self.lvnfs[lvnf_id]
        lvnf.stop()

        # this will update ports and will send lvnf status update message
        self.send_caps_response(lvnf_id)

        del self.lvnfs[lvnf_id]

    def _handle_read_handler_request(self, message):
        """Handle an incoming READ_HANDLER_REQUEST.

        Args:
            message, a READ_HANDLER_REQUEST
        Returns:
            None
        """

        self.dump_message(message)

        lvnf_id = UUID(message['lvnf_id'])
        tenant_id = UUID(message['tenant_id'])
        handler_id = message['handler_id']

        if lvnf_id not in self.lvnfs:
            raise KeyError("LVNF %s not found" % lvnf_id)

        lvnf = self.lvnfs[lvnf_id]

        if 'handler' in message:

            ret = lvnf.read_handler(message['handler'])

            handler = {'handler_id': handler_id,
                       'lvnf_id': lvnf_id,
                       'tenant_id': tenant_id,
                       'retcode': ret[0],
                       'samples': ret[1]}

            self.send_message(PT_READ_HANDLER_RESPONSE, handler)

    def _handle_write_handler_request(self, message):
        """Handle an incoming WRITE_HANDLER_REQUEST.

        Args:
            message, a WRITE_HANDLER_REQUEST
        Returns:
            None
        """

        self.dump_message(message)

        lvnf_id = UUID(message['lvnf_id'])
        tenant_id = UUID(message['tenant_id'])
        handler_id = message['handler_id']

        if lvnf_id not in self.lvnfs:
            raise KeyError("LVNF %s not found" % lvnf_id)

        lvnf = self.lvnfs[lvnf_id]

        if message['value']:
            ret = lvnf.write_handler(message['handler'], message['value'])
        else:
            ret = (200, 'OK')

        handler = {'handler_id': handler_id,
                   'lvnf_id': lvnf_id,
                   'tenant_id': tenant_id,
                   'retcode': ret[0],
                   'samples': ret[1]}

        self.send_message(PT_WRITE_HANDLER_RESPONSE, handler)

    def send_status_lvnf(self, lvnf_id):
        """ Send STATUS FUNCTION message. """

        if lvnf_id not in self.lvnfs:
            raise KeyError("LVNF %s not found" % lvnf_id)

        status = self.lvnfs[lvnf_id].to_dict()
        self.send_message(PT_STATUS_LVNF, status)


def main(Agent=EmpowerAgent):
    """Parse the command line and set the callbacks."""

    usage = "%s [options]" % sys.argv[0]

    parser = ArgumentParser(usage=usage)

    parser.add_argument("-o", "--ofctrl", dest="ofctrl", default=OF_CTRL,
                        help="OpenFlow Controller; default=%s" % OF_CTRL)

    parser.add_argument("-c", "--ctrl", dest="ctrl", default=CTRL_IP,
                        help="Controller address; default=%s" % CTRL_IP)

    parser.add_argument("-p", "--port", dest="port", default=CTRL_PORT,
                        type=int,
                        help="Controller port; default=%u" % CTRL_PORT)

    parser.add_argument("-b", "--bridge", dest="bridge", default=BRIDGE,
                        help="Bridge interface; default='%s'" % BRIDGE)

    parser.add_argument("-t", "--transport", dest="transport", default="ws",
                        help="Specify the transport; default='ws'")

    parser.add_argument("-e", "--every", dest="every", default=DEFAULT_EVERY,
                        help="Heartbeat (in s); default='%u'" % DEFAULT_EVERY)

    parser.add_argument("-l", "--listen", dest="listen", default=CLICK_LISTEN,
                        type=int,
                        help="Click port; default=%u" % CLICK_LISTEN)

    (args, _) = parser.parse_known_args(sys.argv[1:])

    url = "%s://%s:%u/" % (args.transport, args.ctrl, args.port)

    agent = Agent(url, args.ofctrl, args.bridge, args.every, args.listen)
    agent.on_open = on_open
    agent.on_message = on_message
    agent.on_close = on_close

    while True:
        try:
            print("Trying to connect to controller %s" % agent.url)
            agent.run_forever()
            print("Unable to connect, trying again in %us" % agent.every)
            time.sleep(agent.every)
        except KeyboardInterrupt:
            agent.shutdown()
            sys.exit()

if __name__ == "__main__":
    main()
