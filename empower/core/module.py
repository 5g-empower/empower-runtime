#!/usr/bin/env python3
#
# Copyright (c) 2018 Roberto Riggio
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

"""EmPOWER Primitive Base Class."""

import json
import types
import xmlrpc.client

from multiprocessing.pool import ThreadPool

import tornado.web
import tornado.httpserver

from tornado.ioloop import IOLoop

import empower.logger

from empower.core.utils import get_module
from empower.core.jsonserializer import EmpowerEncoder
from empower.main import RUNTIME


_WORKERS = ThreadPool(10)


def exec_xmlrpc(callback, args=()):
    """Execute XML-RPC call."""

    proxy = xmlrpc.client.ServerProxy(callback[0])
    func = getattr(proxy, callback[1])
    run_background(func, on_complete, args)


def run_background(func, callback, args=(), kwds=None):
    """Run callback in background."""

    def _callback(result):
        IOLoop.instance().add_callback(lambda: callback(result))

    _WORKERS.apply_async(func, args, kwds, _callback)


def on_complete(_):
    """XML RPC Callback."""

    pass


class Module:
    """Module object.

    Attributes:
        module_id: A progressive id unique within a given tenant (int)
        module_type: A system-wide unique name for the module
        worker: the module worker responsible for reating new module instances.
        tenant_id: The tenant's Id for convenience (UUID)
        callback: Module callback (FunctionType)
    """

    MODULE_NAME = None
    REQUIRED = ['module_type', 'worker', 'tenant_id']

    def __init__(self):

        self.__tenant_id = None
        self.module_id = 0
        self.module_type = None
        self.worker = None
        self.__callback = None
        self.__periodic = None
        self.log = empower.logger.get_logger()

    def unload(self):
        """Remove this module."""

        self.worker.remove_module(self.module_id)

    def update_db(self, samples):
        """Update InfluxDB with the latest measurements"""

        from empower.statssender.statssender import StatsSender
        stats_sender = get_module(StatsSender.__module__)
        if stats_sender:
            stats_sender.send_stat(points=samples,
                                   database=self.MODULE_NAME,
                                   time_precision='u')

    def handle_callback(self, serializable):
        """Handle an module callback.

        Args:
            serializable, an object implementing the to_dict() method

        Returns:
            None
        """

        # call callback if defined
        if not self.callback:
            return

        callback = self.callback

        try:

            as_dict = serializable.to_dict()
            as_json = json.dumps(as_dict, cls=EmpowerEncoder)

            if isinstance(callback, (types.FunctionType, types.MethodType)):

                callback(serializable)

            elif isinstance(callback, list) and len(callback) == 2:

                exec_xmlrpc(callback, (as_json, ))

            else:

                raise TypeError("Invalid callback type")

        except Exception as ex:

            self.log.exception(ex)

    def as_json(self):
        """Return a JSON representation of the object."""

        return json.dumps(self.to_dict(), cls=EmpowerEncoder, indent=4)

    @property
    def callback(self):
        """ Return this triger callback. """

        return self.__callback

    @callback.setter
    def callback(self, callback=None):
        """Register callback function.

        The callback is generated when the condition is verified. Callback can
        be either a reference to a fucntion or an tuple whose first entry is
        the URL of a remote xmlrpc server and the second entry is the method
        to be called.
        """

        if not callback:
            self.__callback = None
            return

        if isinstance(callback, (types.FunctionType, types.MethodType)):

            self.__callback = callback

        elif isinstance(callback, list) and len(callback) == 2:

            self.__callback = callback

        else:

            raise TypeError("Invalid callback type")

    def start(self):
        """Start worker."""

        self.run_once()

    def stop(self):
        """Stop worker."""

        pass

    def run_once(self):
        """Period task."""

        pass

    def handle_response(self, response):
        """Stub handle response method."""

        pass

    @property
    def tenant_id(self):
        """Return tenant id."""

        return self.__tenant_id

    @tenant_id.setter
    def tenant_id(self, value):
        """ Set tenant id."""

        self.__tenant_id = value

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = {'id': self.module_id,
               'module_type': self.module_type,
               'tenant_id': self.tenant_id,
               'callback': self.callback}

        return out

    def __hash__(self):
        return hash(str(self.tenant_id) + str(self.module_id))

    def __eq__(self, other):

        if isinstance(other, Module):
            return self.module_type == other.module_type and \
                self.tenant_id == other.tenant_id

        return False

    def __str__(self):
        return "Module %u type %s" % (self.module_id, self.module_type)

    def __ne__(self, other):
        return not self.__eq__(other)

class ModuleSingle(Module):
    """Module Single object."""

    pass


class ModuleScheduled(Module):
    """Module Scheduled object."""

    pass


class ModuleTrigger(Module):
    """Module Trigger object."""

    pass


class ModulePeriodic(Module):
    """Module Scheduled object."""

    def __init__(self):
        super().__init__()
        self.__every = 5000

    @property
    def every(self):
        """Return every."""

        return self.__every

    @every.setter
    def every(self, value):
        """Set every."""

        self.__every = int(value)

    def start(self):
        """Start worker."""

        if self.every == -1:
            self.run_once()
            return

        self.__periodic = \
            tornado.ioloop.PeriodicCallback(self.run_once, self.every)
        self.__periodic.start()

    def stop(self):
        """Stop worker."""

        if self.every == -1:
            return

        self.__periodic.stop()

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = {'id': self.module_id,
               'module_type': self.module_type,
               'tenant_id': self.tenant_id,
               'every': self.every,
               'callback': self.callback}

        return out

    def __eq__(self, other):

        if isinstance(other, Module):
            return self.module_type == other.module_type and \
                self.tenant_id == other.tenant_id and \
                self.every == other.every

        return False


class ModuleWorker:
    """Module worker.

    Keeps track of the currently defined modules for each tenant

    Attributes:
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, server, module, pt_type, pt_packet):

        self.__module_id = 0
        self.modules = {}
        self.module = module

        self.pt_type = pt_type
        self.pt_packet = pt_packet
        self.pnfp_server = RUNTIME.components[server]

        self.pnfp_server.register_message(self.pt_type,
                                          self.pt_packet,
                                          self.handle_packet)

        self.log = empower.logger.get_logger()

    @property
    def module_id(self):
        """Return new module id."""

        self.__module_id += 1
        return self.__module_id

    def add_module(self, **kwargs):
        """Add a new module."""

        # check if module type has been set
        if not self.module:
            raise ValueError("Module type not set")

        # add default args
        kwargs['worker'] = self
        kwargs['module_type'] = self.module.MODULE_NAME

        # check if all require parameters have been specified
        for param in self.module.REQUIRED:
            if param not in kwargs:
                raise ValueError("missing %s param" % param)

        # instantiate module
        module = self.module()

        # set mandatory parameters
        for arg in self.module.REQUIRED:
            if not hasattr(module, arg):
                raise ValueError("Invalid param %s" % arg)
            setattr(module, arg, kwargs[arg])

        # set optional parameters
        specified = set(kwargs.keys())
        required = set(self.module.REQUIRED)
        remaining = specified - required
        for arg in remaining:
            if not hasattr(module, arg):
                raise ValueError("Invalid param %s" % arg)
            setattr(module, arg, kwargs[arg])

        # check if an equivalent module has already been defined in the tenant
        for val in self.modules.values():
            # if so return a reference to that trigger
            if val == module:
                return val

        # otherwise generate a new module id
        module.module_id = self.module_id

        # set worker
        module.worker = self

        # add to dict
        self.modules[module.module_id] = module

        # start module
        self.modules[module.module_id].start()

        return module

    def remove_module(self, module_id):
        """Remove a module.

        Args:
            module_id, the tenant id

        Returns:
            None

        Raises:
            KeyError, if module_id is not found
        """

        if module_id not in self.modules:
            self.log.info("Unable to find module (id=%u)", module_id)
            return

        module = self.modules[module_id]

        self.log.info("Removing %s (id=%u)", module.module_type,
                      module.module_id)

        module.stop()

        del self.modules[module_id]

    def handle_packet(self, pnfdev, message):
        """Handle response message."""

        pass
