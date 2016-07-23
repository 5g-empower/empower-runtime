#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""Empower Manager."""

import sys
import getpass
import base64
import json

from http.client import HTTPConnection
from uuid import UUID

from argparse import ArgumentParser


def get_connection(gargs):
    """ Fetch url from option parser. """

    if gargs.transport == "http":
        conn = HTTPConnection(gargs.host, gargs.port)
    else:
        raise ValueError("transport not supported: %s" % gargs.transport)

    if gargs.no_passwd:
        return (conn, {})

    if gargs.passwdfile is None:
        passwd = getpass.getpass("Password: ")
    else:
        passwd = open(gargs.passwdfile, "r").read().strip()

    auth_str = "%s:%s" % (gargs.user, passwd)
    auth = base64.b64encode(auth_str.encode('utf-8'))
    headers = {'Authorization': 'Basic %s' % auth.decode('utf-8')}

    return (conn, headers)


def pa_none(args, cmd):
    """ Null parser method. """

    parser = ArgumentParser(usage=USAGE.format(cmd), description=DESCS[cmd])
    (args, leftovers) = parser.parse_known_args(args)
    return args, leftovers


def pa_component_info(args, cmd):
    """ component info parser method. """

    usage = "%s <component>" % USAGE.format(cmd)
    desc = DESCS[cmd]
    (args, leftovers) = ArgumentParser(usage=usage,
                                       description=desc).parse_known_args(args)
    return args, leftovers


def pa_tenant_component_info(args, cmd):
    """ component info parser method. """

    usage = "%s <tenant_id> <component>" % USAGE.format(cmd)
    desc = DESCS[cmd]
    (args, leftovers) = ArgumentParser(usage=usage,
                                       description=desc).parse_known_args(args)
    return args, leftovers


def pa_load_component(args, cmd):
    """ component info parser method. """

    usage = "%s [<tenant_id>] <component>" % USAGE.format(cmd)
    desc = DESCS[cmd]
    (args, leftovers) = ArgumentParser(usage=usage,
                                       description=desc).parse_known_args(args)
    return args, leftovers


def pa_list_tenant_components(args, cmd):
    """ component info parser method. """

    usage = "%s <tenant_id>" % USAGE.format(cmd)
    desc = DESCS[cmd]
    (args, leftovers) = ArgumentParser(usage=usage,
                                       description=desc).parse_known_args(args)
    return args, leftovers


def pa_feed_on(args, cmd):
    """ component info parser method. """

    usage = "%s <feed id>" % USAGE.format(cmd)
    desc = DESCS[cmd]
    (args, leftovers) = ArgumentParser(usage=usage,
                                       description=desc).parse_known_args(args)
    return args, leftovers


def pa_feed_off(args, cmd):
    """ component info parser method. """

    usage = "%s <feed id>" % USAGE.format(cmd)
    desc = DESCS[cmd]
    (args, leftovers) = ArgumentParser(usage=usage,
                                       description=desc).parse_known_args(args)
    return args, leftovers


def pa_reboot(args, cmd):
    """ Reboot WTP parser method. """

    usage = "%s <wtp>" % USAGE.format(cmd)
    desc = DESCS[cmd]
    (args, leftovers) = ArgumentParser(usage=usage,
                                       description=desc).parse_known_args(args)
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


def do_list_components(gargs, args, leftovers):
    """ List currently defined components. """

    code, data = connect(gargs, ('GET', '/api/v1/components'))

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    for entry in data:
        print(entry)


def do_list_tenant_components(gargs, args, leftovers):
    """ List currently defined components. """

    if len(leftovers) != 1:
        print("Invalid parameter, run help list-tenant-components")
        print_available_cmds()
        sys.exit()

    tenant_id = UUID(leftovers[0])
    url = '/api/v1/tenants/%s/components' % tenant_id
    code, data = connect(gargs, ('GET', url))

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    for entry in data:
        print(entry)


def do_list_wtps(gargs, args, leftovers):
    """ List currently defined components. """

    code, data = connect(gargs, ('GET', '/api/v1/wtps'))

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    for entry in data:

        connection = ""

        if 'connection' in entry and entry['connection']:
            connection = "at %s" % entry['connection'][0]

        line = "%s last seen %s %s" % (entry['addr'],
                                       entry['last_seen'],
                                       connection)

        print(line)


def do_list_feeds(gargs, args, leftovers):
    """ List currently defined components. """

    code, data = connect(gargs, ('GET', '/api/v1/feeds'))

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    for entry in data:

        connection = ""

        if 'mngt' in entry and entry['mngt']:
            connection = "at %s" % entry['mngt'][0]

        status = "n/a"

        for datastream in entry['datastreams']:
            if datastream['id'] == 'switch':
                if datastream['current_value'] == 0.0:
                    status = "on"
                else:
                    status = "off"

        line = "feed %s %s %s" % (entry['id'], connection, status)
        print(line)


def do_component_info(gargs, args, leftovers):
    """ List component info. """

    if len(leftovers) != 1:
        print("Invalid parameter, run help component-info")
        print_available_cmds()
        sys.exit()

    url = '/api/v1/components/%s' % leftovers[0]
    code, data = connect(gargs, ('GET', url))

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    print("componentd_id: %s" % leftovers[0])

    for key, value in data.items():
        print("%s: %s" % (key, value))


def do_tenant_component_info(gargs, args, leftovers):
    """ List component info. """

    if len(leftovers) != 2:
        print("Invalid parameter, run help tenant-component-info")
        print_available_cmds()
        sys.exit()

    url = '/api/v1/tenants/%s/components/%s' % tuple(leftovers)
    code, data = connect(gargs, ('GET', url))

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    print("componentd_id: %s" % leftovers[0])

    for key, value in data.items():
        print("%s: %s" % (key, value))


def do_load_component(gargs, args, leftovers):
    """ List component info. """

    if len(leftovers) == 1:
        url = '/api/v1/components'
    elif len(leftovers) == 2:
        uuid = UUID(leftovers[0])
        url = '/api/v1/tenants/%s/components' % uuid
    else:
        print("Invalid parameter, run help tenant-component-info")
        print_available_cmds()
        sys.exit()

    data = {"version": "1.0", "argv": leftovers[1]}
    code, data = connect(gargs, ('POST', url), data)

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    print("componentd_id: %s" % leftovers[0])

    for key, value in data.items():
        print("%s: %s" % (key, value))


def do_feed_on(gargs, args, leftovers):
    """ List component info. """

    data = {"version": "1.0", "value": "0"}

    code, data = connect(gargs,
                         ('PUT', '/api/v1/feeds/%s' % leftovers[0]),
                         data)

    if code[0] != 204:
        print("%s %s" % code)
        sys.exit()


def do_feed_off(gargs, args, leftovers):
    """ List component info. """

    data = {"version": "1.0", "value": "1"}

    code, data = connect(gargs,
                         ('PUT', '/api/v1/feeds/%s' % leftovers[0]),
                         data)

    if code[0] != 204:
        print("%s %s" % code)
        sys.exit()


def do_reboot(gargs, args, leftovers):
    """ List component info. """

    connection, headers = get_connection(gargs)

    cmd = ('GET', '/api/v1/wtps/%s' % leftovers[0])
    code, data = run_connect(connection, headers, cmd)

    if code[0] != 200:
        print("%s %s" % code)
        sys.exit()

    if 'feed' not in data:
        print("no feed")
        sys.exit()

    feed_id = data['feed']['id']
    cmd = ('PUT', '/api/v1/feeds/%s' % feed_id)

    data = {"version": "1.0", "value": "1"}
    code, data = run_connect(connection, headers, cmd, data)

    if code[0] != 204:
        print("%s %s" % code)
        sys.exit()

    print("feed off")

    data = {"version": "1.0", "value": "0"}
    code, data = run_connect(connection, headers, cmd, data)

    if code[0] != 204:
        print("%s %s" % code)
        sys.exit()

    print("feed on")


def connect(gargs, cmd, data=None):
    """ Run command. """

    connection, headers = get_connection(gargs)
    response, body = run_connect(connection, headers, cmd, data)
    return response, body


def run_connect(connection, headers, cmd, data=None):
    """ Run command. """

    headers['Content-type'] = 'application/json'
    connection.request(cmd[0], cmd[1], headers=headers, body=json.dumps(data))
    response = connection.getresponse()

    str_response = response.read().decode('utf-8')

    if str_response:
        return (response.code, response.reason), json.loads(str_response)
    else:
        return (response.code, response.reason), None


CMDS = {
    'help': (pa_help, do_help),
    'list-components': (pa_none, do_list_components),
    'load-component': (pa_load_component, do_load_component),
    'list-tenant-components': (pa_list_tenant_components,
                               do_list_tenant_components),
    'component-info': (pa_component_info, do_component_info),
    'tenant-component-info': (pa_tenant_component_info,
                              do_tenant_component_info),
    'list-wtps': (pa_none, do_list_wtps),
    'list-feeds': (pa_none, do_list_feeds),
    'feed-on': (pa_feed_on, do_feed_on),
    'feed-off': (pa_feed_off, do_feed_off),
    'reboot': (pa_reboot, do_reboot),
}


USAGE = "%(prog)s {0}"


URL = "%s://%s%s:%s"


DESCS = {
    'help': "Print help message.",
    'load-component': "Load component.",
    'list-components': "List components.",
    'list-tenant-components': "List tenant components.",
    'component-info': "Displays components info.",
    'tenant-component-info': "Displays tenant components info.",
    'list-wtps': "List WTPs.",
    'list-feeds': "List Feeds.",
    'feed-on': "Turn feed on.",
    'feed-off': "Turn feed on.",
    'reboot': "Reboot node.",
}


def parse_global_args(arglist):
    """ Parse global arguments list. """

    usage = "%s [options] command [command_args]" % sys.argv[0]
    args = []

    while len(arglist) != 0 and arglist[0] not in CMDS:
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
                        help="Specify the transport; default='http'")

    (args, _) = parser.parse_known_args(args)

    return args, arglist, parser


def print_available_cmds():
    """ Print list of available commands. """

    cmds = [x for x in CMDS.keys()]
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

    if len(rargs) < 1:
        print("Unknown command")
        print_available_cmds()
        sys.exit()

    (parse_args, do_func) = CMDS[rargs[0]]
    (args, leftovers) = parse_args(rargs[1:], rargs[0])

    do_func(gargs, args, leftovers)


if __name__ == '__main__':
    main()
