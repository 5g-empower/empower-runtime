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

"""Delete LoRaWAN lEndDev from the LNS database."""

import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """Delete LoRaWAN lEndDev parser method.

    usage: empower-ctl.py delete-lenddev <options>

    optional arguments:
      -h, --help            show this help message and exit

    required named arguments:
      -e DEVEUI, --devEUI DEVEUI
                            lEndDev euid
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument(
        "-e", "--devEUI", required=False,
        help="lEndDev euid",
        type=str, dest="devEUI")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Delete a LoRaWAN lEndDev."""

    if args.devEUI:
        url = '/api/v1/lns/lenddevs/%s' % args.devEUI
    else:
        url = '/api/v1/lns/lenddevs'

    command.connect(gargs, ('DELETE', url), 204)
