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

"""Devices CLI tools."""

import empower.cli.command as command


def do_list_wtps(gargs, args, leftovers):
    """ List the WTPs. """

    _, data = command.connect(gargs, ('GET', '/api/v1/wtps'), 200)

    for entry in data.values():

        accum = []

        accum.append("addr ")
        accum.append(entry['addr'])
        accum.append(" desc \"")
        accum.append(entry['desc'])
        accum.append("\"")

        if 'connection' in entry and entry['connection']:
            accum.append(" seq ")
            accum.append(str(entry['last_seen']))
            accum.append(" ip ")
            accum.append(entry['connection']['addr'][0])
            accum.append(" ifaces {")
            ifaces = ["(%s, %s)" % (v['channel'], v['band'])
                      for _, v in entry['blocks'].items()]
            accum.append(', '.join(ifaces))
            accum.append("}")

        print(''.join(accum))


def do_list_vbses(gargs, args, leftovers):
    """ List the VBSes. """

    _, data = command.connect(gargs, ('GET', '/api/v1/vbses'), 200)

    for entry in data.values():

        accum = []

        accum.append("addr ")
        accum.append(entry['addr'])
        accum.append(" desc \"")
        accum.append(entry['desc'])
        accum.append("\"")

        if 'connection' in entry and entry['connection']:
            accum.append(" seq ")
            accum.append(str(entry['last_seen']))
            accum.append(" ip ")
            accum.append(entry['connection']['addr'][0])
            accum.append(" ifaces {")
            ifaces = ["(%s, )" % (v['pci'])
                      for _, v in entry['cells'].items()]
            accum.append(', '.join(ifaces))
            accum.append("}")

        print(''.join(accum))
