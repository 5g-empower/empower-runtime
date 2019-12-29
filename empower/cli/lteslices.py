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

"""LTE SLices CLI tools."""

import uuid
import argparse

import empower.cli.command as command


def pa_list_lte_slices(args, cmd):
    """List lte slices parser method."""

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID, dest="project_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_list_lte_slices(gargs, args, _):
    """List lte slices."""

    url = '/api/v1/projects/%s/lte_slices' % args.project_id
    _, slcs = command.connect(gargs, ('GET', url), 200)

    accum = []

    accum.append("project id ")
    accum.append(str(args.project_id))

    for slc in slcs.values():

        accum.append("\nslice_id ")
        accum.append(str(slc['slice_id']))

        for k, val in slc['properties'].items():
            accum.append("\n    %s: %s" % (k, val))

    print(''.join(accum))


def pa_upsert_lte_slice(args, cmd):
    """Create/update lte slice parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID, dest="project_id")

    required.add_argument('-s', '--slice_id', help='The slice id',
                          required=True, type=int, dest="slice_id")

    parser.add_argument("-r", "--rbgs", dest="rbgs", default=5,
                        help="Number of Resource Blocks Groups",
                        type=int)

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_upsert_lte_slice(gargs, args, _):
    """Create/update lte slice. """

    headers = command.get_headers(gargs)

    request = {
        "version": "1.0",
        "slice_id": args.slice_id,
        "properties": {
            'rbgs': args.rbgs,
            'ue_scheduler': 0
        }
    }

    url = '/api/v1/projects/%s/lte_slices' % args.project_id
    command.connect(gargs, ('POST', url), 201, request, headers=headers)

    url = '/api/v1/projects/%s/lte_slices/%u' % \
        (args.project_id, args.slice_id)
    _, slc = command.connect(gargs, ('GET', url), 200, headers=headers)

    accum = []

    accum.append("slice_id ")
    accum.append(str(slc['slice_id']))

    for k, val in slc['properties'].items():
        accum.append("\n    %s: %s" % (k, val))

    print(''.join(accum))


def pa_delete_lte_slice(args, cmd):
    """Delete lte slice parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID, dest="project_id")

    required.add_argument('-s', '--slice_id', help='The slice id',
                          required=True, type=int, dest="slice_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_delete_lte_slice(gargs, args, _):
    """Delete lte slice. """

    url = '/api/v1/projects/%s/lte_slices/%s' % \
        (args.project_id, args.slice_id)
    command.connect(gargs, ('DELETE', url), 204)

    print(args.slice_id)
