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

"""EmPOWER bootstrap module."""

import logging
import logging.config
import os
import sys
import inspect
import types
import tornado.ioloop

from empower.core.core import EmpowerRuntime

RUNTIME = None


class Options(object):
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

    def _set_log_config(self, given_name, name, value):
        if value is True:
            p = os.path.dirname(os.path.realpath(__file__))
            value = os.path.join(p, "..", "logging.cfg")
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

_HELP_TEXT = """
Start the controller with:
<ctrl-bin>.py [options] [C1 [C1 options]] [C2 [C2 options]] ...

Notable options include:
  --help                Print this help message
  --log-config=<file>   Use log config file (default is ./logging.cfg)

C1, C2, etc. are component names (e.g., Python modules). The supported options
are up to the module.
"""


def _parse_args2(argv, _components, _components_order, _curargs, _options):
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

    _parse_args2(default, _components, _components_order, _curargs, _options)
    _parse_args2(argv, _components, _components_order, _curargs, _options)

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

        component_name = name.split(":")
        launch = "launch"
        name = component_name[0]

        name, module, members = modules[name]
        func = None

        if launch not in members:

            logging.error("%s is not defined in module %s", launch, name)
            return False

        else:

            func = members[launch]

        # We explicitly test for a function and not an arbitrary callable
        if not isinstance(func, types.FunctionType):
            logging.error("%s in %s isn't a function!", launch, name)
            return False

        try:

            if len(component_name) == 2:
                tenant = component_name[1]
                params['tenant'] = tenant
                RUNTIME.register("%s:%s" % (name, tenant), func, params)
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

    if len(names_to_try) == 0:
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
    import empower.main
    empower.main.RUNTIME = EmpowerRuntime()

    # launch components
    if _do_launch(components, components_order):
        _post_startup()
    else:
        raise RuntimeError()

    # start tornado loop
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
