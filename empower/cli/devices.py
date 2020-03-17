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

import argparse

from empower.cli import command

from empower.core.etheraddress import EtherAddress


def pa_del_wtp(args, cmd):
    """Del WTP parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--addr', help='The device address',
                          required=True, type=EtherAddress, dest="addr")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_del_wtp(gargs, args, _):
    """ Del a WTP """

    command.connect(gargs, ('DELETE', '/api/v1/wtps/%s' % args.addr), 204)
    print(args.addr)


def pa_del_vbs(args, cmd):
    """Del VBS parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--addr', help='The device address',
                          required=True, type=EtherAddress, dest="addr")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_del_vbs(gargs, args, _):
    """ Del a VBS """

    command.connect(gargs, ('DELETE', '/api/v1/vbses/%s' % args.addr), 204)
    print(args.addr)


def pa_add_vbs(args, cmd):
    """Add VBS parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--addr', help='The device address',
                          required=True, type=EtherAddress, dest="addr")

    parser.add_argument("-d", "--desc", dest="desc", type=str, default=None,
                        help="A human readable description of the device")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_add_vbs(gargs, args, _):
    """ Add a new VBS """

    request = {
        "version": "1.0",
        "addr": args.addr
    }

    if args.desc:
        request["desc"] = args.desc

    headers = command.get_headers(gargs)

    url = '/api/v1/vbses'
    command.connect(gargs, ('POST', url), 201, request, headers=headers)

    print(args.addr)


def pa_add_wtp(args, cmd):
    """Add WTP parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--addr', help='The device address',
                          required=True, type=EtherAddress, dest="addr")

    parser.add_argument("-d", "--desc", dest="desc", type=str, default=None,
                        help="A human readable description of the device")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_add_wtp(gargs, args, _):
    """ Add a new WTP """

    request = {
        "version": "1.0",
        "addr": args.addr
    }

    if args.desc:
        request["desc"] = args.desc

    headers = command.get_headers(gargs)

    url = '/api/v1/wtps'
    command.connect(gargs, ('POST', url), 201, request, headers=headers)

    print(args.addr)


def do_list_wtps(gargs, *_):
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


def do_list_vbses(gargs, *_):
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
            ifaces = ["(%s)" % (v['pci'])
                      for _, v in entry['cells'].items()]
            accum.append(', '.join(ifaces))
            accum.append("}")

        print(''.join(accum))
