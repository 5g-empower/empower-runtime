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

"""Update a LoRaWAN Gateway in the LNS Database."""

import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """Update lgtw parser method.

    usage: empower-ctl.py update-lgtw <options>

    optional arguments:
      -h, --help            show this help message and exit
      -n NAME, --name NAME  LNS name
      -d DESC, --desc DESC  LNS description
      -o OWNER, --owner OWNER
                            LNS owner; default=None

    required named arguments:
      -e LGTW_EUID, --lgtw_euid LGTW_EUID
                            LNS euid
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument(
        "-e", "--lgtw_euid",
        help="LNS euid",
        type=str, dest="lgtw_euid")

    parser.add_argument(
        '-n', '--name',
        help='LNS name',
        type=str, dest="name")

    parser.add_argument(
        '-d', '--desc',
        help='LNS description',
        type=str, dest="desc")

    parser.add_argument(
        '-o', '--owner',
        help='LNS owner; default=None',
        default=None, type=str, dest="owner")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Update a lgtw."""
    request = {
        "version": "1.0"
    }

    if args.name:
        request["name"] = args.name

    if args.desc:
        request["desc"] = args.desc

    if args.owner:
        request["owner"] = args.owner

    headers = command.get_headers(gargs)

    url = '/api/v1/lns/lgtws/%s' % args.lgtw_euid
    response, _ = command.connect(
        gargs, ('PUT', url), 201, request,
        headers=headers)

    location = response.headers['Location']
    tokens = location.split("/")
    euid = tokens[-1]

    print(euid, " lGTW updated to LNS  Database")
