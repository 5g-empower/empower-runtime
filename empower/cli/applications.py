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

"""Services CLI tools."""

import json
import sys
import uuid
import argparse

import empower.cli.command as command


def pa_list_apps(args, cmd):
    """List applications parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID, dest="project_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_list_apps(gargs, args, _):
    """List currently running application. """

    url = '/api/v1/projects/%s/apps' % args.project_id
    _, data = command.connect(gargs, ('GET', url), 200)

    for entry in data.values():

        accum = []

        accum.append("app id ")
        accum.append(entry['params']['service_id'])
        accum.append(" status RUNNING ")
        accum.append("\n  name: ")
        accum.append(entry['name'])

        accum.append("\n  params:")

        for k, val in entry['params'].items():
            accum.append("\n    %s: %s" % (k, val))

        print(''.join(accum))


def do_list_apps_catalog(gargs, *_):
    """List application that can be loaded. """

    url = '/api/v1/projects/catalog'
    _, data = command.connect(gargs, ('GET', url), 200)

    for entry in data.values():

        accum = []

        accum.append("name ")
        accum.append(entry['name'])
        accum.append("\n")

        accum.append("  desc: ")
        accum.append(entry['desc'])

        accum.append("\n  params:")

        for k, val in entry['params'].items():
            if k in ('service_id', 'project_id'):
                continue
            accum.append("\n    %s: %s" % (k, val['desc']))
            if 'default' in val:
                accum.append(" Default: %s." % val['default'])
            accum.append(" Type: %s." % val['type'])
            accum.append(" Mandatory: %s." % val['mandatory'])

        print(''.join(accum))


def pa_load_app(args, cmd):
    """Load application parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID, dest="project_id")

    required.add_argument('-n', '--name', help='The app name',
                          required=True, type=str, dest="name")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_load_app(gargs, args, leftovers):
    """Load and application. """

    request = {
        "version": "1.0",
        "name": args.name,
        "params": command.get_params(leftovers)
    }

    headers = command.get_headers(gargs)

    url = '/api/v1/projects/%s/apps' % args.project_id
    response, _ = command.connect(gargs, ('POST', url), 201, request,
                                  headers=headers)

    location = response.headers['Location']
    tokens = location.split("/")
    app_id = tokens[-1]

    url = '/api/v1/projects/%s/apps/%s' % (args.project_id, app_id)
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    accum = []

    accum.append("app id ")
    accum.append(data['params']['service_id'])
    accum.append(" status RUNNING ")
    accum.append("\n  name: ")
    accum.append(data['name'])

    accum.append("\n  params:")

    for k, val in data['params'].items():
        accum.append("\n    %s: %s" % (k, val))

    print(''.join(accum))


def pa_unload_app(args, cmd):
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


def do_unload_app(gargs, args, _):
    """Unload and application. """

    url = '/api/v1/projects/%s/apps/%s' % (args.project_id, args.app_id)
    command.connect(gargs, ('DELETE', url), 204)

    print("app id %s status STOPPED" % args.app_id)


def pa_unload_all_apps(args, cmd):
    """Unload application parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-p', '--project_id', help='The project id',
                          required=True, type=uuid.UUID, dest="project_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_unload_all_apps(gargs, args, _):
    """Unload and application. """

    headers = command.get_headers(gargs)

    url = '/api/v1/projects/%s/apps' % args.project_id
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    for entry in data.values():

        app_id = entry['params']['service_id']

        url = '/api/v1/projects/%s/apps/%s' % (args.project_id, app_id)
        command.connect(gargs, ('DELETE', url), 204, headers=headers)

        print("app id %s status STOPPED" % app_id)


def pa_set_app_params(args, cmd):
    """Set application param parser method. """

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


def do_set_app_params(gargs, args, leftovers):
    """Set application parameters. """

    request = {
        "version": "1.0",
        "params": command.get_params(leftovers)
    }

    headers = command.get_headers(gargs)

    url = '/api/v1/projects/%s/apps/%s' % (args.project_id, args.app_id)
    command.connect(gargs, ('PUT', url), 204, request, headers=headers)

    url = '/api/v1/projects/%s/apps/%s' % (args.project_id, args.app_id)
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    accum = []

    accum.append("app id ")
    accum.append(data['params']['service_id'])
    accum.append(" status RUNNING ")
    accum.append("\n  name: ")
    accum.append(data['name'])

    accum.append("\n  params:")

    for k, val in data['params'].items():
        accum.append("\n    %s: %s" % (k, val))

    print(''.join(accum))


def pa_set_app_attribute(args, cmd):
    """Set application attribute parser method. """

    usage = "%s <project_id> <app_id> <attribute> <value>" \
        % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]
    (args, leftovers) = \
        argparse.ArgumentParser(usage=usage,
                                description=desc).parse_known_args(args)
    return args, leftovers


def do_set_app_attribute(gargs, args, leftovers):
    """Set an attribute of an application. """

    if len(leftovers) < 4:
        print("Invalid parameter, run help set-app-attribute")
        command.print_available_cmds()
        sys.exit()

    headers = command.get_headers(gargs)

    project_id = uuid.UUID(leftovers[0])
    app_id = uuid.UUID(leftovers[1])
    attribute = leftovers[2]
    request = json.loads(leftovers[3])

    url = '/api/v1/projects/%s/apps/%s/%s' % (project_id, app_id, attribute)
    command.connect(gargs, ('PUT', url), 204, request, headers=headers)

    print("app id %s attribute %s UPDATED" % (app_id, attribute))
