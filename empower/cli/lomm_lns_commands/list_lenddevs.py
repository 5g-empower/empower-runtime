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

"""List LoRaWAN End Devices in the LNS database."""

import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """List lEndDevs parser method.

    usage: empower-ctl.py list-lenddevs <options>

    optional arguments:
      -h, --help            show this help message and exit
      -g DEVEUI, --devEUI DEVEUI
                            show results for a specified devEUI id only
      -v, --verbose         verbose
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    # required = parser.add_argument_group('required named arguments')

    parser.add_argument(
        '-g', '--devEUI', help='show results for a specified devEUI id only',
        default=None, type=str, dest="devEUI")

    parser.add_argument(
        '-v', '--verbose', help='verbose', action="store_true",
        default=False, dest="config")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """List lEndDevs registered in the LNS."""

    url = '/api/v1/lns/lenddevs/'
    _, data = command.connect(gargs, ('GET', url), 200)

    for entry in data:
        if not args.devEUI:
            print(entry)
        elif entry['DevEUI'] == args.devEUI:
            print(entry)
