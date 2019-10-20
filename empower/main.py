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

"""Bootstrap module."""

import configparser
import ssl
import uuid
import os
import logging
import logging.config
import sys

from importlib import import_module
from argparse import ArgumentParser

import tornado.ioloop

from pymodm.connection import connect
from empower.core.service import EService

DEFAULT_CONFIG = "/etc/empower/empower.cfg"

SERVICES = dict()


def srv_or_die(name):
    """Get a service instance or return None"""

    if name in SERVICES:
        return SERVICES[name]

    logging.error("Unable to find service %s", name)

    sys.exit(1)


def _do_launch(managers, managers_order):
    """Parse arguments and launch controller."""

    # Register managers
    for manager in managers_order:

        module = managers[manager]['module']
        entry_point = managers[manager]['entry_point']
        params = managers[manager]['params']

        if manager in SERVICES:
            logging.error("%s manager already registered", manager)
            return False

        init_method = getattr(import_module(module), entry_point)

        if not issubclass(init_method, EService):
            logging.error("Invalid entry point: %s", manager)
            return False

        logging.info("Loading manager: %s", manager)

        if params:
            logging.info("  - params: %s", params)

        service = init_method(context=None, service_id=uuid.uuid4(), **params)

        SERVICES[manager] = service

    # Start managers
    for manager in managers_order:

        service = SERVICES[manager]

        logging.info("Starting manager: %s", manager)

        # Register handlers for this services
        api_manager = srv_or_die("apimanager")
        for handler in service.HANDLERS:
            api_manager.register_handler(handler)
            handler.service = service

        # start service
        service.start()

    return True


def _setup_db(args):
    """ Setup db connection. """

    config = configparser.ConfigParser()
    config.read(args.empower_config)
    mongodb_uri = config.get('general', 'mongodb',
                             fallback="mongodb://localhost:27017/empower")

    connect(mongodb_uri, ssl_cert_reqs=ssl.CERT_NONE)


def _setup_logging(args):
    """ Setup logging. """

    config = configparser.ConfigParser()
    config.read(args.empower_config)
    log_config = config.get('general', 'log',
                            fallback="/etc/empower/logging.cfg")

    if not os.path.exists(log_config):
        print("Could not find logging config file: %s" % log_config)
        sys.exit(1)

    logging.config.fileConfig(log_config, disable_existing_loggers=False)


def _pre_startup(args):
    """Perform pre-startup operations."""

    _setup_logging(args)
    _setup_db(args)


def _post_startup():
    """Perform post-startup operation."""


def _read_config(args):
    """Read config file."""

    config = configparser.ConfigParser()
    config.read(args.empower_config)

    managers = {}
    managers_order = []

    mngrs = config.get('general', 'managers', fallback=None)

    if not mngrs:
        return managers, managers_order

    for mngr in mngrs.split(","):

        entrypoint = config.get(mngr, 'entrypoint', fallback=None)
        module = config.get(mngr, 'module', fallback=None)

        if not entrypoint or not module:
            continue

        managers_order.append(mngr)

        managers[mngr] = {
            "module": module,
            "entry_point": entrypoint,
            "params": {}
        }

        for param in config[mngr]:

            if param in ('entrypoint', 'module'):
                continue

            managers[mngr][param] = config[mngr][param]

    return managers, managers_order


def _parse_global_args():
    """ Parse global arguments list. """

    parser = ArgumentParser()

    parser.add_argument("-c", "--empower-config",
                        dest="empower_config",
                        default=DEFAULT_CONFIG,
                        help="Configuration file, default: %s" %
                        DEFAULT_CONFIG)

    return parser.parse_known_args(sys.argv[1:])


def main(argv=None):
    """Parses the command line and loads the plugins."""

    # parse command line
    args, _ = _parse_global_args()

    # load managers
    managers, managers_order = _read_config(args)

    # perform pre-startup operation
    _pre_startup(args)

    # launch managers
    if _do_launch(managers, managers_order):
        _post_startup()
    else:
        raise RuntimeError()

    # start tornado loop
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
