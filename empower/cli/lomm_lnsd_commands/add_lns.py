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

"""Add new LNS to the discovery service database."""

import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """Parse the add-lns command.

    usage: empower-ctl.py add-lns <options>

    Add new LNS to the discovery service database.

    optional arguments:
      -h, --help            show this help message and exit
      -o OWNER, --owner OWNER
                            LNS owner; default=None
      -g LGTWS, --lgtws LGTWS
                            add a list of lGTWs to LNS in LNS Discovery
                            database

    required named arguments:
      -n LNS_EUID, --lns_euid LNS_EUID
                            LNS euid
      -d DESC, --desc DESC  LNS description
      -u URI, --uri URI     LNS uri
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument(
        "-n", "--lns_euid", help="LNS euid",
        required=True,
        type=str, dest="lns_euid")

    required.add_argument(
        '-d', '--desc', help='LNS description',
        required=True,
        type=str, dest="desc")

    required.add_argument(
        '-u', '--uri', help='LNS uri',
        required=True,
        type=str, dest="uri")

    parser.add_argument(
        '-o', '--owner', help='LNS owner; default=None',
        type=str, dest="owner")

    parser.add_argument(
        '-g', '--lgtws',
        help='list of lGTWs (comma separated)',
        type=str, dest="lgtws")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Add a new LNS."""

    request = {
        "version": "1.0",
        "desc": args.desc,
        "uri": args.uri,
        "euid": args.lns_euid
    }

    if args.lgtws:
        request["lgtws"] = args.lgtws.split(",")

    if args.owner:
        request["owner"] = args.owner

    response, _ = \
        command.connect(gargs, ('POST', '/api/v1/lnsd/lnss/'), 201, request)

    location = response.headers['Location']
    tokens = location.split("/")
    euid = tokens[-1]

    print(euid)
