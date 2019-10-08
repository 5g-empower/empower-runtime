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


import sys
import uuid
import argparse

import empower.cli.command as command


def do_list_workers(gargs, args, leftovers):
    """List currently running workers. """

    _, data = command.connect(gargs, ('GET', '/api/v1/workers'), 200)

    for entry in data.values():

        accum = []

        accum.append("worker id ")
        accum.append(entry['params']['service_id'])
        accum.append(" status RUNNING ")
        accum.append("\n  name: ")
        accum.append(entry['name'])
        accum.append("\n  params:")

        for k, val in entry['params'].items():
            accum.append("\n    %s: %s" % (k, val))

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

    usage = "%s <worker_name>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]
    (args, leftovers) = \
        argparse.ArgumentParser(usage=usage,
                                description=desc).parse_known_args(args)
    return args, leftovers


def do_load_worker(gargs, args, leftovers):
    """Load and application. """

    params = command.get_params(leftovers)

    if not leftovers:
        print("Invalid parameter, run help load-worker")
        command.print_available_cmds()
        sys.exit()

    request = {
        "version": "1.0",
        "name": leftovers[0],
    }

    if params:
        request['params'] = params

    headers = command.get_headers(gargs)

    url = '/api/v1/workers'
    response, _ = command.connect(gargs, ('POST', url), 201, request,
                                  headers=headers)

    location = response.headers['Location']
    tokens = location.split("/")
    worker_id = tokens[-1]

    url = '/api/v1/workers/%s' % worker_id
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    accum = []

    accum.append("worker id ")
    accum.append(data['params']['service_id'])
    accum.append(" status RUNNING ")
    accum.append("\n  name: ")
    accum.append(data['name'])

    accum.append("\n  params:")

    for k, val in data['params'].items():
        accum.append("\n    %s: %s" % (k, val))

    print(''.join(accum))


def pa_unload_worker(args, cmd):
    """Unload application parser method. """

    usage = "%s <worker_id>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]
    (args, leftovers) = \
        argparse.ArgumentParser(usage=usage,
                                description=desc).parse_known_args(args)
    return args, leftovers


def do_unload_worker(gargs, args, leftovers):
    """Unload and application. """

    if len(leftovers) != 1:
        print("Invalid parameter, run help unload-worker")
        command.print_available_cmds()
        sys.exit()

    worker_id = uuid.UUID(leftovers[0])

    url = '/api/v1/workers/%s' % worker_id
    command.connect(gargs, ('DELETE', url), 204)

    print("worker id %s status STOPPED" % leftovers[0])


def do_unload_all_workers(gargs, args, leftovers):
    """Unload and application. """

    if leftovers:
        print("Invalid parameter, run help unload-all-workers")
        command.print_available_cmds()
        sys.exit()

    headers = command.get_headers(gargs)

    url = '/api/v1/workers'
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    for entry in data.values():

        worker_id = entry['params']['service_id']

        url = '/api/v1/workers/%s' % worker_id
        command.connect(gargs, ('DELETE', url), 204, headers=headers)

        print("worker id %s status STOPPED" % worker_id)


def pa_set_worker_params(args, cmd):
    """Set worker param parser method. """

    usage = "%s <project_id> <worker_id> <params>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]
    (args, leftovers) = \
        argparse.ArgumentParser(usage=usage,
                                description=desc).parse_known_args(args)
    return args, leftovers


def do_set_worker_params(gargs, args, leftovers):
    """Set worker parameters. """

    params = command.get_params(leftovers)

    if len(leftovers) < 2:
        print("Invalid parameter, run help set-worker-params")
        command.print_available_cmds()
        sys.exit()

    request = {
        "version": "1.0",
    }

    if params:
        request['params'] = params

    headers = command.get_headers(gargs)

    worker_id = uuid.UUID(leftovers[1])

    url = '/api/v1/workers/%s' % worker_id
    command.connect(gargs, ('PUT', url), 204, request, headers=headers)

    url = '/api/v1/projects/%s' % worker_id
    _, data = command.connect(gargs, ('GET', url), 200, headers=headers)

    accum = []

    accum.append("worker id ")
    accum.append(data['params']['service_id'])
    accum.append(" status RUNNING ")
    accum.append("\n  name: ")
    accum.append(data['name'])

    accum.append("\n  params:")

    for k, val in data['params'].items():
        accum.append("\n    %s: %s" % (k, val))

    print(''.join(accum))
