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

""" The Agent LVNF. """

import time
import fcntl
import socket
import struct
import subprocess
import re
import threading

from empower.scylla.lvnf import PROCESS_DONE
from empower.scylla.lvnf import PROCESS_RUNNING
from empower.scylla.lvnf import PROCESS_STOPPED


def get_hw_addr(ifname):
    """Fetch hardware address from ifname.

    Retrieve the hardware address of an interface.

    Args:
        ifname: the interface name as a string

    Returns:
        An EtherAddress object

    Raises:
        OSError: An error occured accessing the interface.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    info = fcntl.ioctl(s.fileno(),
                       0x8927,
                       struct.pack('256s', ifname[:15].encode('utf-8')))

    return ':'.join(['%02x' % char for char in info[18:24]])


def exec_cmd(cmd, timeout=2):
    """Execute command and return its output.

    Raise:
        IOError, if the timeout expired or if the command returned and error
    """

    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    try:

        output, errs = proc.communicate(timeout=timeout)

    except subprocess.TimeoutExpired:

        proc.kill()
        output, errs = proc.communicate()

        raise IOError("Unable to run %s: timeout expired" % " ".join(cmd))

    if proc.returncode != 0:
        msg = "Unable to run %s: %s" % (" ".join(cmd), errs.decode('utf-8'))
        raise IOError(msg)

    return output.decode('utf-8')


def write_handler(host, port, handler, value):

    sock = socket.socket()
    sock.connect((host, port))

    f = sock.makefile()
    line = f.readline()

    if line != "Click::ControlSocket/1.3\n":
        raise ValueError("Unexpected reply: %s" % line)

    cmd = "write %s %s\n" % (handler, value)
    sock.send(cmd.encode("utf-8"))

    line = f.readline()

    regexp = '([0-9]{3}) (.*)'
    match = re.match(regexp, line)

    while not match:
        line = f.readline()
        match = re.match(regexp, line)

    groups = match.groups()

    return (int(groups[0]), groups[1])


def read_handler(host, port, handler):

    sock = socket.socket()
    sock.connect((host, port))

    f = sock.makefile()
    line = f.readline()

    if line != "Click::ControlSocket/1.3\n":
            raise ValueError("Unexpected reply: %s" % line)

    cmd = "read %s\n" % handler
    sock.send(cmd.encode("utf-8"))

    line = f.readline()

    regexp = '([0-9]{3}) (.*)'
    match = re.match(regexp, line)

    while not match:
        line = f.readline()
        match = re.match(regexp, line)

    groups = match.groups()

    if int(groups[0]) == 200:

        line = f.readline()
        res = line.split(" ")

        length = int(res[1])
        data = f.read(length)

        return (int(groups[0]), data)

    return (int(groups[0]), line)


class LVNF():
    """A EmPOWER Agent LVNF.

    Attributes:
        agent: pointer to the agent (EmpowerAgent)
        lvnf_id: The virtual network lvnf id (UUID)
        tenant_id: This tenant id (UUID)
        vnf: The virtual network function as a click script (str)
        in_ports: The list of input ports (list)
        out_ports: The list of output ports (list)
        prefix: The virtual network function iface prefix (str)
        script: The complete click script with boilerplate code (str)

    Raises:
        ValueError: If any of the input parameters is invalid
    """

    def __init__(self, agent, lvnf_id, tenant_id, image, bridge, vnf_seq):

        self.agent = agent
        self.lvnf_id = lvnf_id
        self.tenant_id = tenant_id
        self.image = image
        self.bridge = bridge
        self.vnf_seq = vnf_seq
        self.ctrl = 10000 + self.vnf_seq
        self.script = ""
        self.ports = {}
        self.process = None
        self.message = None
        self.thread = None

        # generate boilerplate code (input)
        for i in range(self.image.nb_ports):

            seq = self.vnf_seq
            iface = "vnf-%s-%u-%u" % (self.bridge, seq, i)

            self.ports[i] = {'iface': iface,
                             'hwaddr': None,
                             'virtual_port_id': i,
                             'ovs_port_id': None}

            self.script += "ControlSocket(TCP, %u);\n" % self.ctrl
            self.script += "vnf_in_%u_%u :: FromHost(%s);\n" % (seq, i, iface)
            self.script += "in_%u :: Counter();\n" % i
            self.script += "vnf_in_%u_%u -> in_%u;\n" % (seq, i, i)
            self.script += "vnf_out_%u_%u :: ToHost(%s);\n" % (seq, i, iface)
            self.script += "out_%u :: Counter();\n" % i
            self.script += "out_%u -> vnf_out_%u_%u;\n" % (i, seq, i)

        # append vnf
        self.script += self.image.vnf

    def read_handler(self, handler):
        """Read the handler and return a tuple (code, value)."""

        value = read_handler("127.0.0.1", self.ctrl, handler)

        if value[0] == 200:
            out = [x.strip() for x in value[1].split("\n") if x and x != ""]
            return (200, out)

        return (value[0], value[1])

    def write_handler(self, handler, value):
        """Write the handler(s) and return a tuple (code, message)."""

        if type(value) is list:

            for entry in value:
                ret = write_handler("127.0.0.1", self.ctrl, handler, entry)
                if ret[0] != 200:
                    return (ret[0], ret[1])

            return (ret[0], ret[1])

        else:

            ret = write_handler("127.0.0.1", self.ctrl, handler, value)
            return (ret[0], ret[1])

    def run(self):
        """Start LVNF."""

        print("Starting LVNF %s." % self.lvnf_id)

        try:

            output, errs = self.process.communicate(timeout=0.5)

        except subprocess.TimeoutExpired:

            print("LVNF %s is running pid %u" %
                  (self.lvnf_id, self.process.pid))

            # add interfaces
            self.add_ifaces()

            # this will update ports and will send the lvnf status update
            # message
            self.agent.send_caps_response(self.lvnf_id)

            # this thread is done, start hearbeat thread
            self.thread = threading.Thread(target=self.heartbeat, args=())
            self.thread.signal = True
            self.thread.start()

            return

        print("LVNF %s terminated with code %u" %
              (self.lvnf_id, self.process.returncode))

        print("LVNF error: %s" % errs.decode("utf-8"))

        self.message = errs.decode("utf-8")

        # this will update ports and will send the lvnf status update message
        self.agent.send_caps_response(self.lvnf_id)

    def heartbeat(self):
        """Check process status."""

        while self.thread.signal:

            self.process.poll()

            if self.process.returncode is not None:

                print("LVNF %s: process is not running." % self.lvnf_id)

                try:
                    outs, errs = self.process.communicate(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    outs, errs = self.process.communicate(timeout=0.5)

                print("LVNF %s terminated with code %u" %
                      (self.lvnf_id, self.process.returncode))

                print("LVNF error: %s" % errs.decode("utf-8"))

                self.message = errs.decode("utf-8")

                self.remove_ifaces()

                # this will update ports and will send the lvnf status update
                # message
                self.agent.send_caps_response(self.lvnf_id)

                return

            time.sleep(2)

        print("Terminating LVNF %s heartbeat" % self.lvnf_id)

    def start(self):
        """Start click daemon."""

        print("Starting LVNF %s" % self.lvnf_id)
        print(self)

        self.process = subprocess.Popen(["click", "-e", self.script],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

        threading.Thread(target=self.run, args=()).start()

    def stop(self):
        """Stop click daemon."""

        print("Stopping LVNF %s" % self.lvnf_id)

        # stop heartbeat thread
        if self.thread:
            self.thread.signal = False

        if self.process and self.process.returncode is None:
            self.process.kill()

        self.process = None
        self.remove_ifaces()

        print("LVNF %s stopped" % self.lvnf_id)

    def add_ifaces(self):
        """Add ifaces to bridge."""

        for virtual_port_id in self.ports:

            iface = self.ports[virtual_port_id]['iface']

            print("Adding virtual port %u (%s) to bridge %s" %
                  (virtual_port_id, iface, self.agent.bridge))

            exec_cmd(["ifconfig", iface, "up"])
            exec_cmd(["ovs-vsctl", "add-port", self.agent.bridge, iface])

            ovs_port_id = None
            for port in self.agent.ports.values():
                if port['iface'] == iface:
                    ovs_port_id = port['port_id']
                    break

            self.ports[virtual_port_id]['hwaddr'] = get_hw_addr(iface)
            self.ports[virtual_port_id]['ovs_port_id'] = ovs_port_id

    def remove_ifaces(self):
        """Remove ifaces from bridge."""

        for virtual_port_id in self.ports:

            iface = self.ports[virtual_port_id]['iface']

            print("Removing virtual port %u (%s) from bridge %s" %
                  (virtual_port_id, iface, self.agent.bridge))

            try:
                exec_cmd(["ovs-vsctl", "del-port", self.agent.bridge, iface])
            except OSError:
                print("Unable to remove port %s" % iface)

        self.ports = {}

    def to_dict(self):
        """Return a JSON-serializable dictionary."""

        out = {'lvnf_id': self.lvnf_id,
               'tenant_id': self.tenant_id,
               'image': self.image.to_dict(),
               'vnf_seq': self.vnf_seq,
               'ctrl': self.ctrl,
               'script': self.script,
               'ports': self.ports}

        if not self.process:
            out['process'] = PROCESS_STOPPED
            return out

        if self.process.returncode is None:
            out['process'] = PROCESS_RUNNING
        else:
            out['process'] = PROCESS_DONE
            out['returncode'] = self.process.returncode
            out['message'] = self.message

        return out

    def __eq__(self, other):
        if isinstance(other, LVNF):
            return self.lvnf_id == other.lvnf_id
        return False

    def __str__(self):
        """ Return a string representation of the VNF."""

        return "LVNF %s (ports=[%s])\n%s" % \
            (self.lvnf_id,
             ",".join([str(x) for x in self.ports.keys()]),
             self.script.strip())
