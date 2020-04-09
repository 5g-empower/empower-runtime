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

"""Add new LoRaWAN Gateway to the LNS database."""

import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """Add lgtw parser method.

    usage: empower-ctl.py add-lgtw <options>

    optional arguments:
      -h, --help            show this help message and exit
      -d DESC, --desc DESC  lGTW description
      -o OWNER, --owner OWNER
                            lGTW owner; default=None

    required named arguments:
      -e LGTW_EUID, --lgtw_euid LGTW_EUID
                            lGTW euid
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument(
        "-e", "--lgtw_euid", help="lGTW euid",
        required=True,
        type=str, dest="lgtw_euid")

    parser.add_argument(
        '-d', '--desc', help='lGTW description',
        default="Generic LoRaWAN GTW",
        type=str, dest="desc")

    parser.add_argument(
        '-o', '--owner', help='lGTW owner; default=None',
        type=str, dest="owner")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Add a new lgtw."""

    request = {
        "version": "1.0",
        "desc": args.desc
    }

    if args.owner:
        request["owner"] = args.owner

    url = '/api/v1/lns/lgtws/%s' % args.lgtw_euid

    response, _ = command.connect(gargs, ('POST', url), 201, request)

    location = response.headers['Location']
    tokens = location.split("/")
    euid = tokens[-1]

    print("lGTW %s added to LNS Database" % euid)
