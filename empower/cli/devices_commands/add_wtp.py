#!/usr/bin/env python3
#
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

"""Add a new WTP."""

import argparse

from empower.cli import command

from empower.core.etheraddress import EtherAddress


def pa_cmd(args, cmd):
    """Add WTP parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--addr', help='The device address',
                          required=True, type=EtherAddress, dest="addr")

    parser.add_argument("-d", "--desc", dest="desc", type=str,
                        default="Generic WTP",
                        help="A human readable description of the device")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """ Add a new WTP """

    request = {
        "addr": args.addr,
        "desc": args.desc
    }

    command.connect(gargs, ('POST', '/api/v1/wtps'), 201, request)

    print(args.addr)
