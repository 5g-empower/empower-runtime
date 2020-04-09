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

"""Delete LoRaWAN lGTW from the LNS database."""

import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """Delete LoRaWAN lGTW parser method.

    usage: empower-ctl.py delete-lgtw <options>

    optional arguments:
      -h, --help            show this help message and exit

    required named arguments:
      -e LGTW_EUID, --lgtw_euid LGTW_EUID
                            lGTW euid
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument(
        "-e", "--lgtw_euid", required=False,
        help="lGTW euid",
        type=str, dest="lgtw_euid")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Delete a LoRaWAN lGTW."""

    if args.lgtw_euid:
        url = '/api/v1/lns/lgtws/%s' % args.lgtw_euid
    else:
        url = '/api/v1/lns/lgtws'

    command.connect(gargs, ('DELETE', url), 204)
