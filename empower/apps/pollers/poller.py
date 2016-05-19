#!/usr/bin/env python3
#
# Copyright (c) 2016, Roberto Riggio
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

"""Poller Apps."""

import psutil

from empower.core.app import EmpowerApp


class Poller(EmpowerApp):
    """Base EmPOWER poller application. Use it to stress-test pollers.

    Command Line Parameters:

        pool: network id (mandatory)
        filepath: path to the CSVs output directory (optional, default ./)
        every: loop period in ms (optional, default 5000ms)

    """

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.filepath = "./"

    def loop(self):
        """ Periodic job. """

        # save cpu and memory utilization
        for proc in psutil.process_iter():
            if proc.name() != 'python3':
                continue

            cpu = proc.cpu_percent()
            mem = proc.memory_info()[0] / (1024 * 1024)

            line = "%f,%u\n" % (cpu, mem)

            filename = self.filepath + "cpu_%u.csv" % self.every

            with open(filename, 'a') as file_d:
                file_d.write(line)

        # Save signalling channel bytes
        for wtp in self.wtps():

            if not wtp.connection:
                continue

            line = "%s,%u,%u\n" % (wtp.addr,
                                   wtp.downlink_bit_rate,
                                   wtp.uplink_bit_rate)

            filename = self.filepath + "signalling_%u.csv" % self.every

            with open(filename, 'a') as file_d:
                file_d.write(line)
