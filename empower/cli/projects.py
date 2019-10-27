#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""Projects CLI tools."""

import uuid
import argparse

import empower.cli.command as command

from empower.core.plmnid import PLMNID
from empower.core.ssid import SSID


def pa_delete_project(args, cmd):
    """Delete project parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID)

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_delete_project(gargs, args, _):
    """Delete a project. """

    url = '/api/v1/projects/%s' % args.project_id
    command.connect(gargs, ('DELETE', url), 204)
    print(args.project_id)


def pa_create_project(args, cmd):
    """Create project parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-d', '--desc', help='The project description',
                          required=True, type=str, dest="desc")

    required.add_argument('-o', '--owner', help='The project owner',
                          required=True, type=str, dest="owner")

    parser.add_argument("-c", "--mcc", dest="mcc", default=None,
                        help="The network MCC; default=None",
                        type=str)

    parser.add_argument("-n", "--mnc", dest="mcc", default=None,
                        help="The network MNC; default=None",
                        type=str)

    parser.add_argument("-s", "--ssid", dest="ssid", default=None,
                        help="The network SSID; default=None",
                        type=SSID)

    parser.add_argument("-t", "--ssid_type", dest="ssid_type",
                        default="unique", choices=["unique", "shared"],
                        help="The network SSID type; default=unique")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_create_project(gargs, args, _):
    """ Add a new Project """

    request = {
        "version": "1.0",
        "desc": args.desc,
        "owner": args.owner
    }

    if args.ssid:

        request["wifi_props"] = {
            "bssid_type": args.ssid_type,
            "ssid": args.ssid
        }

    if args.mcc and args.mnc:

        plmnid = PLMNID(args.mcc, args.mnc)

        request["lte_props"] = {
            "plmnid": plmnid.to_dict()
        }

    headers = command.get_headers(gargs)

    url = '/api/v1/projects'
    response, _ = command.connect(gargs, ('POST', url), 201, request,
                                  headers=headers)

    location = response.headers['Location']
    tokens = location.split("/")
    project_id = tokens[-1]

    print(project_id)


def do_list_projects(gargs, *_):
    """List currently running workers. """

    _, data = command.connect(gargs, ('GET', '/api/v1/projects'), 200)

    for entry in data.values():

        accum = []

        accum.append("project_id ")

        accum.append(entry['project_id'])

        accum.append(" desc \"%s\"" % entry['desc'])

        if 'wifi_props' in entry and entry['wifi_props']:
            accum.append(" ssid \"%s\"" % entry['wifi_props']['ssid'])

        if 'lte_props' in entry and entry['lte_props']:
            accum.append(" plmnid \"%s\"" % entry['lte_props']['plmnid'])

        print(''.join(accum))
