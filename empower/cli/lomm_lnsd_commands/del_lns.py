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

"""Delete LoRaWAN LNS from the discovery service."""

import uuid
import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """Delete LNS parser method.

    usage: empower-ctl.py delete-lns <options>

    Delete LoRaWAN LNS from the discovery service.

    optional arguments:
      -h, --help            show this help message and exit
      -p PROJECT_ID, --project_id PROJECT_ID
                            project id

    required named arguments:
      -e LNS_EUID, --lns_euid LNS_EUID
                            LNS euid
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument(
        "-e", "--lns_euid", help="LNS euid",
        required=True,
        type=str, dest="lns_euid")

    parser.add_argument(
        '-p', '--project_id', help='project id',
        type=uuid.UUID, dest="project_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Delete an LNS."""
    # if args.project_id:
    #   url = '/api/v1/projects/%s/lnss/%s' % args.project_id, args.lns_euid
    # else:
    #   url = '/api/v1/lnsd/lnss/%s' % args.lns_euid
    url = '/api/v1/lnsd/lnss/%s' % args.lns_euid
    command.connect(gargs, ('DELETE', url), 204)
    print(args.lns_euid)
