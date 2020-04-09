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

"""List LoRaWAN LNSs in the discovery service."""

import uuid
import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """List LNSs parser method.

    usage: empower-ctl.py list-lnss <options>

    List LoRaWAN LNSs in the discovery service.

    optional arguments:
      -h, --help            show this help message and exit
      -l, --lgtws           list lGTWs in the discovery service database
      -n LNS_EUID, --lns_euid LNS_EUID
                            show results for the specified LNS id only
      -g LGTW_EUID, --lgtw_euid LGTW_EUID
                            show results for the specified lGTW id only
      -p PROJECT_ID, --project_id PROJECT_ID
                            project id
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    parser.add_argument(
        '-n', '--lns_euid', help='show results for the specified LNS id only',
        type=str, dest="lns_euid")

    parser.add_argument(
        '-p', '--project_id', help='project id',
        type=uuid.UUID, dest="project_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """List LNSs in the discovery service database."""

    # if args.project_id:
    #   url = '/api/v1/projects/%s/lnss' % args.project_id
    # else:
    #   url = '/api/v1/lnsd/lnss'

    if args.lns_euid:

        url = "/api/v1/lnsd/lnss/" + args.lns_euid
        _, entry = command.connect(gargs, ('GET', url), 200)
        out = ""
        for key in entry:
            value = "None"
            if entry[key]:
                if isinstance(entry[key], list):
                    value = "'" + ",'".join(entry[key]) + "'"
                else:
                    value = "'" + str(entry[key]) + "'"
            out += key + ":" + value + " "
        print(out)

        return

    url = "/api/v1/lnsd/lnss"
    _, data = command.connect(gargs, ('GET', url), 200)
    for entry in data.values():
        out = ""
        for key in entry:
            value = "None"
            if entry[key]:
                if isinstance(entry[key], list):
                    value = "'" + ",'".join(entry[key]) + "'"
                else:
                    value = "'" + str(entry[key]) + "'"
            out += key + ":" + value + " "
        print(out)
