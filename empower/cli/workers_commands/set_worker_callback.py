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

"""Set worker callback."""

import uuid
import argparse

import empower_core.command as command

from empower_core.service import CALLBACK_REST


def pa_cmd(args, cmd):
    """Set worker callback parser method."""

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-u', '--uuid', help='The worker id',
                          required=True, type=uuid.UUID, dest="uuid")

    required.add_argument('-n', '--name', help='The name of the callback',
                          required=True, type=str, dest="name")

    required.add_argument('-c', '--callback', help='The URL of the callback',
                          required=True, type=str, dest="callback")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Set worker callback."""

    request = {
        "version": "1.0",
        "name": args.name,
        "callback_type": CALLBACK_REST,
        "callback": args.callback
    }

    headers = command.get_headers(gargs)
    url = '/api/v1/workers/%s/callbacks' % args.uuid
    command.connect(gargs, ('POST', url), 201, request, headers=headers)

    url = '/api/v1/workers/%s/callbacks/%s' % (args.uuid, args.name)

    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    print(data)
