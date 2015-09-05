#!/usr/bin/env python3
#
# Copyright (c) 2016, Roberto Riggio
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

"""A proof-of-concept python app leveraging the EmPOWER rest interface."""

import sys
import getpass
import base64
import json

from xmlrpc.server import SimpleXMLRPCServer
from http.client import HTTPSConnection
from http.client import HTTPConnection
from argparse import ArgumentParser


CONNECTION = None
SERVER = None
HEADERS = None
XMLRPC_URL = None
TENANT_ID = None


def convert(f):

    def new_f(*args, **kwargs):

        new_args = []
        new_kwargs = {}

        for arg in args:
            new_args.append(json.loads(arg))

        for kwarg in kwargs:
            new_kwargs[kwarg] = json.loads(kwargs[kwarg])

        f(*new_args, **new_kwargs)

    new_f.__name__ = f.__name__

    return new_f


def get_connection(args):
    """ Fetch url from option parser. """

    if args.transport == "http":
        connection = HTTPConnection(args.host, args.port)
    elif args.transport == "https":
        connection = HTTPSConnection(args.host, args.port)
    else:
        raise ValueError("transport not supported: %s" % args.transport)

    if args.no_passwd:
        return (connection, {})

    if args.passwdfile is None:
        passwd = getpass.getpass("Password: ")
    else:
        passwd = open(args.passwdfile, "r").read().strip()

    auth_str = "%s:%s" % (args.user, passwd)
    auth = base64.b64encode(auth_str.encode('utf-8'))
    headers = {'Authorization': 'Basic %s' % auth.decode('utf-8')}

    return (connection, headers)


def execute(connection, headers, cmd, data=None):
    """ Run command. """

    headers['Content-type'] = 'application/json'
    connection.request(cmd[0], cmd[1], headers=headers, body=json.dumps(data))
    response = connection.getresponse()

    resp = response.readall().decode('utf-8')

    if resp:
        return (response.code, response.reason), json.loads(resp)
    else:
        return (response.code, response.reason), None


def synch_callback(url):

    cmd = ('GET', url)

    response, body = execute(CONNECTION, HEADERS, cmd)

    if response[0] != 200:
        print("%s %s" % response)
        sys.exit()

    for entry in body:
        if 'callback' in entry:
            callback = entry['callback'][1]
            func = globals()[callback]
            SERVER.register_function(func)


def cpp_up(callback):

    SERVER.register_function(callback)
    data = {"version": "1.0", "callback": (XMLRPC_URL, callback.__name__)}

    cmd = ('POST', '/api/v1/tenants/%s/cppup' % TENANT_ID)

    response, body = execute(CONNECTION, HEADERS, cmd, data)

    if response[0] != 201:
        print("%s %s" % response)
        sys.exit()


@convert
def cpp_up_callback(cpp):

    print("CPP %s is up" % cpp['addr'])


def main():
    """ Parse argument list and execute command. """

    global CONNECTION
    global SERVER
    global HEADERS
    global XMLRPC_URL
    global TENANT_ID

    usage = "%s [options]" % sys.argv[0]

    parser = ArgumentParser(usage=usage)

    parser.add_argument("-x", "--xmlrpc", dest="xmlrpc",
                        default="http://127.0.0.1:8000/RPC2",
                        help="Specify the XML-RPC server URL")

    parser.add_argument("-a", "--hostname", dest="host", default="127.0.0.1",
                        help="EmPOWER REST address; default='127.0.0.1'")

    parser.add_argument("-p", "--port", dest="port", default="8888",
                        help="EmPOWER REST port; default=8888")

    parser.add_argument("-u", "--user", dest="user", default="root",
                        help="EmPOWER admin user; default='root'")

    parser.add_argument("-n", "--no-passwd", action="store_true",
                        dest="no_passwd", default=False,
                        help="Run without password; default false")

    parser.add_argument("-f", "--passwd-file", dest="passwdfile",
                        default=None, help="Password file; default=none")

    parser.add_argument("-i", "--tenant-id", dest="tenant_id",
                        default=None, help="Tenant id; default=none")

    parser.add_argument("-t", "--transport", dest="transport", default="http",
                        help="Specify the transport; default='http'")

    (args, _) = parser.parse_known_args(sys.argv[1:])

    CONNECTION, HEADERS = get_connection(args)

    SERVER = SimpleXMLRPCServer(("localhost", 8000))
    XMLRPC_URL = args.xmlrpc
    TENANT_ID = args.tenant_id

    # synch state
    synch_callback(url='/api/v1/tenants/%s/cppup' % args.tenant_id)

    # register callback
    cpp_up(callback=cpp_up_callback)

    # Start xml-rpc server
    SERVER.serve_forever()


if __name__ == '__main__':
    main()
