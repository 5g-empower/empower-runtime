#!/usr/bin/env python3
#
# Copyright (c) 2019 Fondazione Bruno Kessler
# Author(s): Roberto Riggio (rriggio@fbk.eu), Cristina Costa (ccosta@fbk.eu)
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

"""Command Line Interface."""

import sys
import base64
import getpass
import json
import pkgutil
import importlib

from argparse import ArgumentParser

import requests

from requests.exceptions import ConnectionError as RequestConnectionError

import empower.cli

from empower.core.serialize import serialize

from empower.cli.projects import do_list_projects, do_create_project, \
    pa_create_project, do_delete_project, pa_delete_project

from empower.cli.wifislices import pa_list_wifi_slices, do_list_wifi_slices, \
    pa_upsert_wifi_slice, do_upsert_wifi_slice, pa_delete_wifi_slice, \
    do_delete_wifi_slice

from empower.cli.lteslices import pa_list_lte_slices, do_list_lte_slices, \
    pa_upsert_lte_slice, do_upsert_lte_slice, pa_delete_lte_slice, \
    do_delete_lte_slice

from empower.cli.applications import pa_list_apps, do_list_apps, \
    do_list_apps_catalog, pa_load_app, do_load_app, pa_unload_app, \
    do_unload_app, pa_unload_all_apps, do_unload_all_apps, pa_set_app_params, \
    do_set_app_params

from empower.cli.workers import do_list_workers, do_list_workers_catalog, \
    pa_load_worker, do_load_worker, pa_unload_worker, do_unload_worker, \
    do_unload_all_workers, pa_set_worker_params, do_set_worker_params

USAGE = "%(prog)s {0}"
URL = "%s://%s%s:%s"

DESCS = {}
CMDS = {}

for _, name, is_pkg in pkgutil.walk_packages(empower.cli.__path__):

    if is_pkg and name.endswith("_commands"):

        package = importlib.import_module("empower.cli." + name)
        pkgs = pkgutil.walk_packages(package.__path__)

        for _, module_name, _ in pkgs:

            module = importlib.import_module(package.__name__ + "." +
                                             module_name)

            cmd_name = module.NAME

            CMDS[cmd_name] = [None, None]
            DESCS[cmd_name] = ""

            if hasattr(module, "PARSER"):
                CMDS[cmd_name][0] = getattr(module, module.PARSER)

            if hasattr(module, "EXEC"):
                CMDS[cmd_name][1] = getattr(module, module.EXEC)

            if hasattr(module, "DESC"):
                DESCS[cmd_name] = module.DESC


def connect(gargs, cmd, expected=200, request=None,
            headers=None, exit_on_err=True):
    """ Run command. """

    if not headers:
        headers = get_headers(gargs)

    url = "%s://%s:%s" % (gargs.transport, gargs.host, gargs.port)
    method = getattr(requests, cmd[0].lower())

    response = method(url + cmd[1], headers=headers, json=serialize(request))

    try:
        data = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        data = {}

    if response.status_code != expected:

        msg = "%u: %s (%s)" % \
            (data['status_code'], data['title'], data['detail'])

        if exit_on_err:
            print(msg)
            sys.exit()
        else:
            raise Exception(msg)

    return response, data


def get_headers(gargs):
    """Get the required headers. """

    headers = {
        'Content-type': 'application/json'
    }

    if gargs.no_passwd:
        return headers
    if gargs.passwdfile is not None:
        passwd = open(gargs.passwdfile, "r").read().strip()
        auth_str = "%s:%s" % (gargs.user, passwd)
    elif gargs.auth is not None:
        auth_str = gargs.auth
    else:
        passwd = getpass.getpass("Password: ")
        auth_str = "%s:%s" % (gargs.user, passwd)

    auth = base64.b64encode(auth_str.encode('utf-8'))

    headers['Authorization'] = 'Basic %s' % auth.decode('utf-8')

    return headers


def get_params(leftovers):
    """Turn arguments leftovers into service params."""

    params = {}

    for param in leftovers:
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


CMDS.update({
    'list-apps-catalog': (pa_none, do_list_apps_catalog),
    'list-workers-catalog': (pa_none, do_list_workers_catalog),

    'create-project': (pa_create_project, do_create_project),
    'delete-project': (pa_delete_project, do_delete_project),
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

    'load-worker': (pa_load_worker, do_load_worker),
    'unload-worker': (pa_unload_worker, do_unload_worker),
    'unload-all-workers': (pa_none, do_unload_all_workers),
    'set-worker-params': (pa_set_worker_params, do_set_worker_params),

})

DESCS.update({

    'create-project': "Create a new project.",
    'delete-project': "Delete a project.",

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
    'delete-lte-slice': "Delete an LTE slice",

    'worker-info': "Show the details of a worker",
    'application-info': "Show the details of an application",

    'load-app': "Load an application",
    'unload-app': "Unload an application",
    'unload-all-apps': "Unload all applications",
    'set-app-params': "Set application parameters",

    'load-worker': "Load a worker",
    'unload-worker': "Unload a worker",
    'unload-all-workers': "Unload all workers",
    'set-worker-params': "Set worker parameter",
})


def parse_global_args(arglist):
    """ Parse global arguments list. """

    usage = "%s [options] command [command options]" % sys.argv[0]

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
    parser.add_argument("-a", "--auth", dest="auth", default=None,
                        help="EmPOWER admin user:passw")
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
    if 'help' in cmds:
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

    if parse_args:
        (args, leftovers) = parse_args(rargs[1:], rargs[0])
    else:
        (args, leftovers) = pa_none(rargs[1:], rargs[0])

    if leftovers and rargs[0] != "help":
        print("Warning - unknown parameters: ", ', '.join(leftovers))

    if do_func:
        try:
            do_func(gargs, args, leftovers)
        except RequestConnectionError:
            print("Failed to establish a connection with the Controller")


if __name__ == '__main__':
    main()
