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

"""Workers CLI tools."""

import uuid
import argparse

from empower.cli import command

from empower.core.service import CALLBACK_REST


def do_list_workers(gargs, args, leftovers):
    """List currently running workers. """

    _, data = command.connect(gargs, ('GET', '/api/v1/workers'), 200)

    for entry in data.values():

        accum = []

        accum.append("worker_id ")
        accum.append(entry['service_id'])
        accum.append(" name ")
        accum.append(entry['name'])

        print(''.join(accum))


def do_list_workers_catalog(gargs, args, leftovers):
    """List workers that can be loaded. """

    _, data = command.connect(gargs, ('GET', '/api/v1/catalog'), 200)

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


def pa_load_worker(args, cmd):
    """Load application parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-n', '--name', help='The app name',
                          required=True, type=str, dest="name")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_load_worker(gargs, args, leftovers):
    """Load and application. """

    request = {
        "version": "1.0",
        "name": args.name,
        "params": command.get_params(leftovers)
    }

    headers = command.get_headers(gargs)

    url = '/api/v1/workers'
    response, _ = command.connect(gargs, ('POST', url), 201, request,
                                  headers=headers)

    location = response.headers['Location']
    tokens = location.split("/")
    worker_id = tokens[-1]

    url = '/api/v1/workers/%s' % worker_id
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    print(data['service_id'])


def pa_unload_worker(args, cmd):
    """Unload application parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--worker_id', help='The worker id',
                          required=True, type=uuid.UUID, dest="worker_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_unload_worker(gargs, args, _):
    """Unload and application. """

    url = '/api/v1/workers/%s' % args.worker_id
    command.connect(gargs, ('DELETE', url), 204)

    print(args.worker_id)


def do_unload_all_workers(gargs, args, leftovers):
    """Unload and application. """

    headers = command.get_headers(gargs)

    url = '/api/v1/workers'
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    for entry in data.values():

        worker_id = entry['service_id']

        url = '/api/v1/workers/%s' % worker_id
        command.connect(gargs, ('DELETE', url), 204, headers=headers)

        print(worker_id)


def pa_set_worker_params(args, cmd):
    """Set worker param parser method. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--worker_id', help='The worker id',
                          required=True, type=uuid.UUID, dest="worker_id")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_set_worker_params(gargs, args, leftovers):
    """Set worker parameters. """

    request = {
        "version": "1.0",
        "params": command.get_params(leftovers)
    }

    headers = command.get_headers(gargs)

    url = '/api/v1/workers/%s' % args.worker_id
    command.connect(gargs, ('PUT', url), 204, request, headers=headers)

    url = '/api/v1/workers/%s' % args.worker_id
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    accum = []

    accum.append("worker_id ")
    accum.append(data['service_id'])
    accum.append("\n  name ")
    accum.append(data['name'])

    accum.append("\n  params:")

    for k, val in data['params'].items():
        accum.append("\n    %s: %s" % (k, val))

    print(''.join(accum))


def pa_add_callback(args, cmd):
    """Add a callback. """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    required = parser.add_argument_group('required named arguments')

    required.add_argument('-a', '--worker_id', help='The worker id',
                          required=True, type=uuid.UUID, dest="worker_id")

    required.add_argument('-n', '--name', help='The name of the callback',
                          required=True, type=str, dest="name")

    required.add_argument('-c', '--callback', help='The URL of the callback',
                          required=True, type=str, dest="callback")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_add_callback(gargs, args, leftovers):
    """Add a callback. """

    request = {
        "version": "1.0",
        "name": args.name,
        "callback_type": CALLBACK_REST,
        "callback": args.callback
    }

    headers = command.get_headers(gargs)
    url = '/api/v1/workers/%s/callbacks' % args.worker_id
    command.connect(gargs, ('POST', url), 201, request, headers=headers)

    url = '/api/v1/workers/%s/callbacks/%s' % (args.worker_id, args.name)

    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    print(data)
