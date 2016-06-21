#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""Poller Apps."""

import psutil

from empower.core.app import EmpowerApp


class Poller(EmpowerApp):
    """Base EmPOWER poller application. Use it to stress-test pollers.

    Command Line Parameters:

        tenant_id: network id (mandatory)
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
