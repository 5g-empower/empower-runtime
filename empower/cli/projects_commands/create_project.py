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

"""Create a new project."""

import argparse

import empower_core.command as command

from empower_core.plmnid import PLMNID
from empower_core.ssid import SSID


def pa_cmd(args, cmd):
    """Create project parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-d', '--desc', help='The project description',
                          required=True, type=str, dest="desc")

    required.add_argument('-o', '--owner', help='The project owner',
                          required=True, type=str, dest="owner")

    parser.add_argument("-c", "--plmnid", dest="plmnid", default=None,
                        help="The network PLMNID; default=None",
                        type=str)

    parser.add_argument("-s", "--ssid", dest="ssid", default=None,
                        help="The network SSID; default=None",
                        type=SSID)

    parser.add_argument("-t", "--ssid_type", dest="ssid_type",
                        default="unique", choices=["unique", "shared"],
                        help="The network SSID type; default=unique")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """ Add a new Project """

    request = {
        "desc": args.desc,
        "owner": args.owner
    }

    if args.ssid:

        request["wifi_props"] = {
            "bssid_type": args.ssid_type,
            "ssid": args.ssid
        }

    if args.plmnid:

        plmnid = PLMNID(args.plmnid)

        request["lte_props"] = {
            "plmnid": plmnid.to_str()
        }

    headers = command.get_headers(gargs)

    url = '/api/v1/projects'
    response, _ = command.connect(gargs, ('POST', url), 201, request,
                                  headers=headers)

    location = response.headers['Location']
    tokens = location.split("/")
    project_id = tokens[-1]

    print(project_id)
