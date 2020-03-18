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

"""Print help message."""

import argparse
import sys

from empower.cli import command


def pa_cmd(args, cmd):
    """ Help option parser. """

    usage = "%s <cmd>" % command.USAGE.format(cmd)
    (args, leftovers) = \
        argparse.ArgumentParser(usage=usage).parse_known_args(args)
    return args, leftovers


def do_cmd(gargs, args, leftovers):
    """ Help execute method. """

    if len(leftovers) != 1:
        print("No command specified")
        command.print_available_cmds()
        sys.exit()

    try:
        (parse_args, _) = command.CMDS[leftovers[0]]
        parse_args(['--help'], leftovers[0])
    except KeyError:
        print("Invalid command: %s is an unknown command." % leftovers[0])
        sys.exit()
