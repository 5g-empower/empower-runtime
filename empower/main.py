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

"""EmPOWER bootstrap module."""

from uuid import UUID
from ipaddress import ip_address

import logging
import logging.config
import os
import sys
import inspect
import types
import tornado.ioloop

from empower.core.core import EmpowerRuntime

RUNTIME = None


class Options:
    """Options parser."""

    def set(self, given_name, value):
        """Parse incoming options."""

        name = given_name.replace("-", "_")
        if name.startswith("_") or hasattr(Options, name):
            logging.error("Illegal option: %s", given_name)
            return False

        has_field = hasattr(self, name)
        has_setter = hasattr(self, "_set_" + name)
        if has_field is False and has_setter is False:
            logging.error("Unknown option: %s", given_name)
            return False
        if has_setter:
            setter = getattr(self, "_set_" + name)
            setter(given_name, name, value)
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


class EmpowerOptions(Options):
    """Global EmPOWER options."""

    def __init__(self):
        self.log_config = None
        self.ctrl_adv = False
        self.ctrl_ip = ip_address("192.168.100.158")
        self.ctrl_port = 5533
        self.ctrl_adv_iface = "wlp2s0"

    def _set_ctrl_port(self, given_name, name, value):
        self.ctrl_port = int(value)

    def _set_ctrl_ip(self, given_name, name, value):
        self.ctrl_ip = ip_address(value)

    def _set_ctrl_adv(self, given_name, name, value):
        self.ctrl_adv = value

    def _set_log_config(self, given_name, name, value):
        if value is True:
            log_p = os.path.dirname(os.path.realpath(__file__))
            value = os.path.join(log_p, "..", "logging.cfg")
        self.log_config = value

    @classmethod
    def _set_help(cls, *_):
        """ Print help text and exit. """

        print(_HELP_TEXT)
        sys.exit(0)

    @classmethod
    def _set_h(cls, *_):
        """ Print help text and exit. """

        print(_HELP_TEXT)
        sys.exit(0)


_OPTIONS = EmpowerOptions()

_HELP_TEXT = """Start the controller with:
<ctrl-bin>.py [options] [C1 [C1 options]] [C2 [C2 options]] ...

Notable options include:
  --help                Print this help message
  --log-config=<file>   Use log config file (default is ./logging.cfg)
  --ctrl-adv            Advertise controller (bool, default is false)
  --ctrl-ip=<ip>        Controller address (ip, default is 192.168.100.158)
  --ctrl-port=<port>    Controller port (int, default is 5533)

C1, C2, etc. are component names (e.g., Python modules). The supported options
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

    for name in components_order:

        params = components[name]
        launch = "launch"
        name, _, members = modules[name]

        if launch not in members:
            logging.error("%s is not defined in module %s", launch, name)
            return False

        func = members[launch]

        # We explicitly test for a function and not an arbitrary callable
        if not isinstance(func, types.FunctionType):
            logging.error("%s in %s isn't a function!", launch, name)
            return False

        try:

            if 'tenant_id' in params:
                params['tenant_id'] = UUID(params['tenant_id'])
                RUNTIME.register_app(name, func, params)
            else:
                RUNTIME.register(name, func, params)

        except TypeError as ex:
            logging.error("Error calling %s in %s: %s", launch, name, ex)
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

    if name in sys.modules:
        return name

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

    pass


def main(argv=None):
    """Parses the command line and loads the plugins."""

    components, components_order = _parse_args(sys.argv[1:], argv)

    # perform pre-startup operation, e.g. logging setup
    _pre_startup()

    # Set the runtime after logging has been configured. This must be done
    # here since the components loader requires this symbol to be defined.
    global RUNTIME
    RUNTIME = EmpowerRuntime(_OPTIONS)

    # launch components
    if _do_launch(components, components_order):
        _post_startup()
    else:
        raise RuntimeError()

    # start tornado loop
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
