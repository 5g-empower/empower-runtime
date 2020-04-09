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

"""List LoRaWAN lGTWs in the LNS database."""

import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """List lGTWs parser method.

    usage: empower-ctl.py list-lgtws <options>

    optional arguments:
      -h, --help            show this help message and exit
      -g LGTW_EUID, --lgtw_euid LGTW_EUID
                            show results for specified lGTW id only
      -c, --config          show config data
      -r, --version         show version data
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    # required = parser.add_argument_group('required named arguments')

    parser.add_argument(
        '-g', '--lgtw_euid', help='show results for specified lGTW id only',
        default=None, type=str, dest="lgtw_euid")

    parser.add_argument(
        '-c', '--config', help='show config data', action="store_true",
        default=False, dest="config")

    parser.add_argument(
        '-r', '--version', help='show version data', action="store_true",
        default=False, dest="version")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """List lGTWs registered in the LNS."""

    url = '/api/v1/lns/lgtws'
    _, data = command.connect(gargs, ('GET', url), 200)

    for entry in data:
        out = "name "
        out += entry['name']
        out += " lgtw_euid "
        out += entry['lgtw_euid']
        out += " desc "
        out += "'" + entry['desc'] + "'"

        if not args.lgtw_euid:
            print(out)
            if args.config:
                print("config: " + str(entry["lgtw_config"]))

            if args.version:
                print("version: " + str(entry["lgtw_version"]))

        elif entry['lgtw_euid'] == args.lgtw_euid:
            print(out)

            if args.config:
                print("config: " + str(entry["lgtw_config"]))

            if args.version:
                print("version: " + str(entry["lgtw_version"]))
