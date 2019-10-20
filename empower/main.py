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

import ssl
import uuid
import os
import logging
import logging.config
import sys

from importlib import import_module

import tornado.ioloop

from pymodm.connection import connect
from empower.core.service import EService

DEFAULT_MONGODB_URI = "mongodb://localhost:27017/empower"
DEFAULT_LOG_CONFIG = "/etc/empower/logging.cfg"

SERVICES = dict()


class Options:
    """Options parser."""

    def set(self, name, value):
        """Parse incoming options."""

        if name.startswith("_") or hasattr(Options, name):
            logging.error("Illegal option: %s", name)
            return False

        has_field = hasattr(self, name)
        has_setter = hasattr(self, "_set_" + name)
        if has_field is False and has_setter is False:
            logging.error("Unknown option: %s", name)
            return False
        if has_setter:
            setter = getattr(self, "_set_" + name)
            setter(name, value)
        else:
            if isinstance(getattr(self, name), bool):
                # Automatic bool-ization
                value = bool(value)
            setattr(self, name, value)
        return True

    def process_options(self, options):
        """Process incoming options."""

        for key, value in options.items():
            if self.set(key, value) is False:
                sys.exit(1)


class EOptions(Options):
    """EmPOWER ptions parser."""

    def __init__(self):
        self.log_config = DEFAULT_LOG_CONFIG
        self.mongodb_uri = DEFAULT_MONGODB_URI

    def _set_log_config(self, name, value):
        setattr(self, name, value)

    def _set_mongodb_uri(self, name, value):
        setattr(self, name, value)

    @classmethod
    def _set_help(cls, *_):
        """ Print help text and exit. """

        print(_HELP_TEXT % (DEFAULT_LOG_CONFIG, DEFAULT_MONGODB_URI))

        sys.exit(0)

    @classmethod
    def _set_h(cls, *_):
        """ Print help text and exit. """

        print(_HELP_TEXT % (DEFAULT_LOG_CONFIG, DEFAULT_MONGODB_URI))

        sys.exit(0)


_OPTIONS = EOptions()

_HELP_TEXT = """Start with:
empower-runtime.py [options] [C1 [C1 options]] [C2 [C2 options]] ...

Notable options include:
  --help                Print this help message
  --log-config=<file>   Use log config file (default is %s)
  --mongodb_uri=<uri>   Specify MongoDB URI (default is %s)

C1, C2, etc. are managers' names (e.g., Python modules). The supported options
are up to the module.
"""


def _parse_args2(argv, _components, _components_order, _curargs):
    """Parse command line arguments."""

    for arg in argv:
        if not arg.startswith("-"):
            if arg not in _components:
                _components[arg] = {}
            _curargs = _components[arg]
            if arg not in _components_order:
                _components_order.append(arg)
        else:
            arg = arg.lstrip("-").split("=", 1)
            arg[0] = arg[0].replace("-", "_")
            if len(arg) == 1:
                arg.append(True)
            _curargs[arg[0]] = arg[1]


def _parse_args(argv, default=None):
    """Parse command line arguments."""

    _components_order = []
    _components = {}

    _curargs = {}
    _options = _curargs

    if default:
        _parse_args2(default, _components, _components_order, _curargs)

    _parse_args2(argv, _components, _components_order, _curargs)

    _OPTIONS.process_options(_options)

    return _components, _components_order


def _do_launch(components, components_order):
    """Parse arguments and launch controller."""

    # Register managers
    for component in components_order:

        params = components[component]

        short_name = component.split(':')[0]
        name = component.split(':')[1]
        entry_point = component.split(':')[2]

        if short_name in SERVICES:
            logging.error("%s manager already registered", component)
            raise ValueError("%s manager already registered" % component)

        init_method = getattr(import_module(name), entry_point)

        if not issubclass(init_method, EService):
            logging.error("Invalid entry point: %s", component)
            return False

        logging.info("Loading manager: %s", name)

        if params:
            logging.info("  - params: %s", params)

        service = init_method(context=None, service_id=uuid.uuid4(), **params)

        SERVICES[short_name] = service

    # Start managers
    for component in components_order:

        short_name = component.split(':')[0]

        service = SERVICES[short_name]

        logging.info("Starting manager: %s", short_name)

        # Register handlers for this services
        api_manager = srv_or_die("apimanager")
        for handler in service.HANDLERS:
            api_manager.register_handler(handler)
            handler.service = service

        # start service
        service.start()

    return True


def _setup_db():
    """ Setup db connection. """

    logging.info("Connecting to MongoDB: %s", _OPTIONS.mongodb_uri)
    connect(_OPTIONS.mongodb_uri, ssl_cert_reqs=ssl.CERT_NONE)


def _setup_logging():
    """ Setup logging. """

    log_handler = logging.StreamHandler()
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    log_handler.setFormatter(formatter)
    logging.getLogger().addHandler(log_handler)
    logging.getLogger().setLevel(logging.INFO)

    if _OPTIONS.log_config:

        if not os.path.exists(_OPTIONS.log_config):
            print("Could not find logging config file:", _OPTIONS.log_config)
            sys.exit(2)

        logging.config.fileConfig(_OPTIONS.log_config,
                                  disable_existing_loggers=False)


def _pre_startup():
    """Perform pre-startup operation.

    This function is called after all the options have been parsed but
    before any components is loaded.
    """

    _setup_db()
    _setup_logging()


def _post_startup():
    """Perform post-startup operation.

    This function is called after all components are loaded. Everything goes
    smoothly in this method then the tornado loop is started.
    """


def srv_or_die(name):
    """Get a service instance or return None"""

    if name in SERVICES:
        return SERVICES[name]

    logging.error("Unable to find service %s", name)

    sys.exit(1)


def main(argv=None):
    """Parses the command line and loads the plugins."""

    components, components_order = _parse_args(sys.argv[1:], argv)

    # perform pre-startup operation, e.g. logging setup
    _pre_startup()

    # launch components
    if _do_launch(components, components_order):
        _post_startup()
    else:
        raise RuntimeError()

    # start tornado loop
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
