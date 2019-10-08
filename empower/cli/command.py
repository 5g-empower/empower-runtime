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

"""5G-EmPOWER Command Line Interface."""

import sys
import base64
import getpass
import json

from argparse import ArgumentParser

import requests

from empower.cli.devices import do_list_wtps, do_list_vbses

from empower.cli.projects import do_list_projects

from empower.cli.wifislices import pa_list_wifi_slices, do_list_wifi_slices, \
    pa_upsert_wifi_slice, do_upsert_wifi_slice, pa_delete_wifi_slice, \
    do_delete_wifi_slice

from empower.cli.lteslices import pa_list_lte_slices, do_list_lte_slices, \
    pa_upsert_lte_slice, do_upsert_lte_slice, pa_delete_lte_slice, \
    do_delete_lte_slice

from empower.cli.applications import pa_list_apps, do_list_apps, \
    do_list_apps_catalog, pa_load_app, do_load_app, pa_unload_app, \
    do_unload_app, pa_unload_all_apps, do_unload_all_apps, pa_set_app_params, \
    do_set_app_params, pa_set_app_attribute, do_set_app_attribute

from empower.cli.workers import do_list_workers, do_list_workers_catalog, \
    pa_load_worker, do_load_worker, pa_unload_worker, do_unload_worker, \
    do_unload_all_workers, pa_set_worker_params, do_set_worker_params


def connect(gargs, cmd, expected=200, request=None, headers=None):
    """ Run command. """

    if not headers:
        headers = get_headers(gargs)

    url = "%s://%s:%s" % (gargs.transport, gargs.host, gargs.port)
    method = getattr(requests, cmd[0].lower())

    response = method(url + cmd[1], headers=headers, json=request)

    try:
        data = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        data = {}

    if response.status_code != expected:

        if 'message' in data:
            msg = "Result: %u %s (%s)" % \
                (data['status_code'], data['reason'], data['message'])
        else:
            msg = "Result: %u %s" % (data['status_code'], data['reason'])

        print(msg)

        sys.exit()

    return response, data


def get_headers(gargs):
    """Get the required headers. """

    headers = {
        'Content-type': 'application/json'
    }

    if gargs.no_passwd:
        return headers

    if gargs.passwdfile is None:
        passwd = getpass.getpass("Password: ")
    else:
        passwd = open(gargs.passwdfile, "r").read().strip()

    auth_str = "%s:%s" % (gargs.user, passwd)
    auth = base64.b64encode(auth_str.encode('utf-8'))

    headers['Authorization'] = 'Basic %s' % auth.decode('utf-8')

    return headers


def get_params(leftovers):
    """Turn arguments leftovers into service params."""

    params = {}

    for param in leftovers[2:]:
        tokens = param.split("=")
        if len(tokens) != 2:
            continue
        key = tokens[0].replace("--", "")
        value = tokens[1]
        params[key] = value

    return params


def pa_none(args, cmd):
    """ Null parser method. """

    parser = ArgumentParser(usage=USAGE.format(cmd), description=DESCS[cmd])
    (args, leftovers) = parser.parse_known_args(args)
    return args, leftovers


def pa_help(args, cmd):
    """ Help option parser. """

    usage = "%s <cmd>" % USAGE.format(cmd)
    (args, leftovers) = ArgumentParser(usage=usage).parse_known_args(args)
    return args, leftovers


def do_help(gargs, args, leftovers):
    """ Help execute method. """

    if len(leftovers) != 1:
        print("No command specified")
        print_available_cmds()
        sys.exit()

    try:
        (parse_args, _) = CMDS[leftovers[0]]
        parse_args(['--help'], leftovers[0])
    except KeyError:
        print("Invalid command: %s is an unknown command." % leftovers[0])
        sys.exit()


CMDS = {
    'help': (pa_help, do_help),

    'list-apps-catalog': (pa_none, do_list_apps_catalog),
    'list-workers-catalog': (pa_none, do_list_workers_catalog),

    'list-wtps': (pa_none, do_list_wtps),
    'list-vbses': (pa_none, do_list_vbses),

    'list-projects': (pa_none, do_list_projects),

    'list-workers': (pa_none, do_list_workers),
    'list-apps': (pa_list_apps, do_list_apps),

    'list-wifi-slices': (pa_list_wifi_slices, do_list_wifi_slices),
    'upsert-wifi-slice': (pa_upsert_wifi_slice, do_upsert_wifi_slice),
    'delete-wifi-slice': (pa_delete_wifi_slice, do_delete_wifi_slice),

    'list-lte-slices': (pa_list_lte_slices, do_list_lte_slices),
    'upsert-lte-slice': (pa_upsert_lte_slice, do_upsert_lte_slice),
    'delete-lte-slice': (pa_delete_lte_slice, do_delete_lte_slice),

    'load-app': (pa_load_app, do_load_app),
    'unload-app': (pa_unload_app, do_unload_app),
    'unload-all-apps': (pa_unload_all_apps, do_unload_all_apps),
    'set-app-params': (pa_set_app_params, do_set_app_params),
    'set-app-attribute': (pa_set_app_attribute, do_set_app_attribute),

    'load-worker': (pa_load_worker, do_load_worker),
    'unload-worker': (pa_unload_worker, do_unload_worker),
    'unload-all-workers': (pa_none, do_unload_all_workers),
    'set-worker-params': (pa_set_worker_params, do_set_worker_params),

}


USAGE = "%(prog)s {0}"


URL = "%s://%s%s:%s"


DESCS = {
    'help': "Print help message.",

    'list-wtps': "List WTPs.",
    'list-vbses': "List VBSes.",
    'list-workers': "List active workers.",
    'list-projects': "List projects.",
    'list-workers-catalog': "List available workers.",
    'list-apps': "List active apps.",
    'list-apps-catalog': "List available apps.",

    'list-wifi-slices': "List Wi-Fi slices.",
    'upsert-wifi-slice': "Create/Update a Wi-Fi slice",
    'delete-wifi-slice': "Delete a Wi-Fi slice",

    'list-lte-slices': "List LTE slices.",
    'upsert-lte-slice': "Create/Update a LTE slice",
    'delete-lte-slice': "Delete a LTE slice",

    'worker-info': "Show the details of a worker",
    'application-info': "Show the details of an application",

    'load-app': "Load an application",
    'unload-app': "Unload an application",
    'unload-all-apps': "Unload all applications",
    'set-app-params': "Set application parameters",
    'set-app-attribute': "Set an attribute of an app",

    'load-worker': "Load a worker",
    'unload-worker': "Unload a worker",
    'unload-all-workers': "Unload all workers",
    'set-worker-params': "Set worker parameter",
}


def parse_global_args(arglist):
    """ Parse global arguments list. """

    usage = "%s [options] command [command_args]" % sys.argv[0]
    args = []

    while arglist and arglist[0] not in CMDS:
        args.append(arglist[0])
        arglist.pop(0)

    parser = ArgumentParser(usage=usage)

    parser.add_argument("-r", "--host", dest="host", default="127.0.0.1",
                        help="REST server address; default='127.0.0.1'")
    parser.add_argument("-p", "--port", dest="port", default="8888",
                        help="REST server port; default=8888")
    parser.add_argument("-u", "--user", dest="user", default="root",
                        help="EmPOWER admin user; default='root'")
    parser.add_argument("-n", "--no-passwd", action="store_true",
                        dest="no_passwd", default=False,
                        help="Run without password; default false")
    parser.add_argument("-f", "--passwd-file", dest="passwdfile",
                        default=None, help="Password file; default=none")
    parser.add_argument("-t", "--transport", dest="transport", default="http",
                        help="The transport (http/https); default='http'")

    (args, _) = parser.parse_known_args(args)

    return args, arglist, parser


def print_available_cmds():
    """ Print list of available commands. """

    cmds = list(CMDS.keys())
    cmds.remove('help')
    cmds.sort()
    print("\nAvailable commands are: ")
    for cmd in cmds:
        print("   {0:25}     {1:10}".format(cmd, DESCS[cmd]))
    print("\nSee '%s help <command>' for more info." % sys.argv[0])


def main():
    """ Parse argument list and execute command. """

    (gargs, rargs, parser) = parse_global_args(sys.argv[1:])

    if len(sys.argv) == 1:
        print(parser.format_help().strip())
        print_available_cmds()
        sys.exit()

    if not rargs:
        print("Unknown command")
        print_available_cmds()
        sys.exit()

    (parse_args, do_func) = CMDS[rargs[0]]
    (args, leftovers) = parse_args(rargs[1:], rargs[0])

    do_func(gargs, args, leftovers)


if __name__ == '__main__':
    main()
