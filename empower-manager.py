#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" The Empower Manager. """

import sys
import getpass
import base64
import json

from http.client import HTTPSConnection
from http.client import HTTPConnection

from argparse import ArgumentParser


def get_connection(gargs):
    """ Fetch url from option parser. """

    if gargs.transport == "http":
        connection = HTTPConnection(gargs.host, gargs.port)
    elif gargs.transport == "https":
        connection = HTTPSConnection(gargs.host, gargs.port)
    else:
        raise ValueError("transport not supported: %s" % gargs.transport)

    if gargs.no_passwd:
        return (connection, {})

    if gargs.passwdfile is None:
        passwd = getpass.getpass("Password: ")
    else:
        passwd = open(gargs.passwdfile, "r").read().strip()

    auth_str = "%s:%s" % (gargs.user, passwd)
    auth = base64.b64encode(auth_str.encode('utf-8'))
    headers = {'Authorization': 'Basic %s' % auth.decode('utf-8')}

    return (connection, headers)


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
        raise ValueError

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

    code, data = connect(gargs,
                         ('GET', '/api/v1/components/%s' % leftovers[0]))

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

    str_response = response.readall().decode('utf-8')

    if str_response:
        return (response.code, response.reason), json.loads(str_response)
    else:
        return (response.code, response.reason), None


CMDS = {
    'help': (pa_help, do_help),
    'list-components': (pa_none, do_list_components),
    'component-info': (pa_component_info, do_component_info),
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
    'list-components': "List components.",
    'component-info': "Displays components info.",
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

    parser.add_argument("-a", "--hostname", dest="host", default="127.0.0.1",
                        help="Specify the EmPOWER host; default='127.0.0.1'")
    parser.add_argument("-p", "--port", dest="port", default="8888",
                        help="Specify the EmPOWER web port; default=8888")
    parser.add_argument("-u", "--user", dest="user", default="root",
                        help="EmPOWER admin user; default='root'")
    parser.add_argument("-n", "--no-passwd", action="store_true",
                        dest="no_passwd", default=False,
                        help="Run empowerctl with no password; default false")
    parser.add_argument("-f", "--passwd-file", dest="passwdfile",
                        default=None, help="Password file; default=none")
    parser.add_argument("-t", "--transport", dest="transport", default="http",
                        help="Specify the transport; default='http'")

    (args, _) = parser.parse_known_args(args)

    return args, arglist, parser


def print_available_cmds(parser):
    """ Print list of available commands. """

    cmds = [x for x in CMDS.keys()]
    cmds.remove('help')
    cmds.sort()
    print(parser.format_help().strip())
    print("\n Available commands are: ")
    for cmd in cmds:
        print("   {0:25}     {1:10}".format(cmd, DESCS[cmd]))
    print("\n See '%s help <command>' for more info." % sys.argv[0])


def main():
    """ Parse argument list and execute command. """

    try:

        (gargs, rargs, parser) = parse_global_args(sys.argv[1:])

        if len(rargs) < 1:
            raise IndexError

        (parse_args, do_func) = CMDS[rargs[0]]
        (args, leftovers) = parse_args(rargs[1:], rargs[0])

        do_func(gargs, args, leftovers)

    except IndexError:

        print("%s is an unknown command" % sys.argv[-1])
        print_available_cmds(parser)
        sys.exit()

    except ValueError:

        print("Invalid parameters for command %s" % sys.argv[-1])
        print_available_cmds(parser)
        sys.exit()

if __name__ == '__main__':
    main()
