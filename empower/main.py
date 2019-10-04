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

import uuid
import inspect
import os
import logging
import logging.config
import sys
import types
import tornado.ioloop

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
    """5 options."""

    def __init__(self):
        self.log_config = DEFAULT_LOG_CONFIG

    def _set_log_config(self, name, value):
        setattr(self, name, value)

    @classmethod
    def _set_help(cls, *_):
        """ Print help text and exit. """

        print(_HELP_TEXT % (DEFAULT_LOG_CONFIG))

        sys.exit(0)

    @classmethod
    def _set_h(cls, *_):
        """ Print help text and exit. """

        print(_HELP_TEXT % (DEFAULT_LOG_CONFIG))

        sys.exit(0)


_OPTIONS = EOptions()

_HELP_TEXT = """Start with:
empower-runtime.py [options] [C1 [C1 options]] [C2 [C2 options]] ...

Notable options include:
  --help                Print this help message
  --log-config=<file>   Use log config file (default is %s)

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

    modules = _do_imports(n.split(':')[0] for n in components_order)

    if modules is False:
        logging.error("No modules to import!")
        return False

    # Register components
    for name in components_order:

        params = components[name]
        name, _, members = modules[name]

        if "launch" not in members:
            logging.error("Property 'launch' not defined in module %s", name)
            return False

        launch = members["launch"]

        # We explicitly test for a function and not an arbitrary callable
        if not isinstance(launch, types.FunctionType):
            logging.error("Property 'launch' in %s isn't a function!", name)
            return False

        try:

            if name in SERVICES:
                logging.error("%s service already registered", name)
                raise ValueError("%s service already registered" % name)

            logging.info("Registering service: %s", name)
            params['service_id'] = uuid.uuid4()
            params['project_id'] = uuid.uuid4()
            service = launch(**params)

            SERVICES[name] = service

        except TypeError as ex:
            logging.error("Error calling %s in %s", launch, name)
            logging.exception(ex)
            return False

    # Start components
    for name in components_order:

        name, _, _ = modules[name]

        try:

            service = SERVICES[name]

            logging.info("Starting service: %s", name)

            # Register handlers for this services
            api_manager = srv_or_die("empower.managers.apimanager.apimanager")
            for handler in service.HANDLERS:
                api_manager.register_handler(handler)
                handler.service = service

            # start service
            SERVICES[name].start()

        except TypeError as ex:
            logging.error("Error starting service %s", name)
            logging.exception(ex)
            return False

    return True


def _do_import(base_name):
    """Try to import the named component.

    Returns its module name if it was loaded or False on failure.
    """

    names_to_try = ["empower" + "." + base_name, base_name]

    if not names_to_try:
        logging.error("Module not found: %s", base_name)
        return False

    name = names_to_try.pop(0)

    try:
        logging.info("Importing module: %s", name)
        __import__(name, level=0)
        return name
    except ImportError as ex:
        logging.info("Could not import module: %s", name)
        logging.exception(ex)
        return False


def _do_imports(components):
    """Import listed components.

    Returns map of component_name->name,module,members on success, or False on
    failure
    """

    done = {}
    for name in components:
        if name in done:
            continue
        result = _do_import(name)
        if result is False:
            return False
        members = dict(inspect.getmembers(sys.modules[result]))
        done[name] = (result, sys.modules[result], members)

    return done


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
