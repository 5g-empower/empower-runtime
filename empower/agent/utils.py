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

"""The EmPOWER Agent Utils."""

import fcntl
import socket
import struct
import re
import subprocess


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
