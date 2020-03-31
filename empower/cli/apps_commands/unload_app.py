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

"""Unload an application. """

import uuid
import argparse

from empower.cli import command


def pa_cmd(args, cmd):
    """Unload application parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID, dest="project_id")

    required.add_argument('-a', '--app_id', help='The app id',
                          required=True, type=uuid.UUID, dest="app_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Unload an application. """

    url = '/api/v1/projects/%s/apps/%s' % (args.project_id, args.app_id)
    command.connect(gargs, ('DELETE', url), 204)

    print(args.app_id)
