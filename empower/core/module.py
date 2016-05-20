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

"""EmPOWER Primitive Base Class."""

import re
import json
import types
import xmlrpc.client

import tornado.web
import tornado.httpserver
from tornado.ioloop import IOLoop

from uuid import UUID
from multiprocessing.pool import ThreadPool

import empower.logger

from empower.core.jsonserializer import EmpowerEncoder
from empower.restserver.apihandlers import EmpowerAPIHandlerUsers
from empower.restserver.restserver import RESTServer
from empower.lvapp.lvappserver import LVAPPServer
from empower.lvnfp.lvnfpserver import LVNFPServer

from empower.main import RUNTIME

LOG = empower.logger.get_logger()


_WORKERS = ThreadPool(10)


def exec_xmlrpc(callback, args=()):
    """Execute XML-RPC call."""

    LOG.info("Calling %s:%s", callback[0], callback[1])

    proxy = xmlrpc.client.ServerProxy(callback[0])
    func = getattr(proxy, callback[1])
    run_background(func, on_complete, args)


def run_background(func, callback, args=(), kwds={}):
    """Run callback in background."""

    def _callback(result):
        IOLoop.instance().add_callback(lambda: callback(result))

    _WORKERS.apply_async(func, args, kwds, _callback)


def on_complete(res):
    """XML RPC Callback."""

    pass


class ModuleHandler(EmpowerAPIHandlerUsers):
    """ModuleHandler. Used to view and manipulate modules."""

    def get(self, *args, **kwargs):
        """List all modules or just the specified one.

        Args:
            [0]: tenant_id
            [1]: module_id

        Example URLs:

            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/<module>
            GET /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/<module>/1
        """

        try:

            if len(args) > 2 or len(args) < 1:
                raise ValueError("Invalid URL")
            tenant_id = UUID(args[0])

            resp = {k: v for k, v in self.server.modules.items()
                    if v.tenant_id == tenant_id}

            if len(args) == 1:
                self.write_as_json(resp.values())
            else:
                module_id = int(args[1])
                self.write_as_json(resp[module_id])
        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

    def post(self, *args, **kwargs):
        """Create a new module.

        Args:
            [0]: tenant_id

        Request:
            version: the protocol version (1.0)

        Example URLs:

            POST /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/<module>
        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid URL")

            tenant_id = UUID(args[0])

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            del request['version']
            request['tenant_id'] = tenant_id
            request['module_type'] = self.server.module.MODULE_NAME
            request['worker'] = self.server

            module = self.server.add_module(**request)

            self.set_header("Location", "/api/v1/tenants/%s/%s/%s" %
                            (module.tenant_id,
                             self.server.module.MODULE_NAME,
                             module.module_id))

            self.set_status(201, None)

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)

    def delete(self, *args, **kwargs):
        """Delete a module.

        Args:
            [0]: tenant_id
            [1]: module_id

        Example URLs:

            DELETE /api/v1/tenants/52313ecb-9d00-4b7d-b873-b55d3d9ada26/
              <module>/1
        """

        try:

            if len(args) != 2:
                raise ValueError("Invalid URL")

            tenant_id = UUID(args[0])
            module_id = int(args[1])

            module = self.server.modules[module_id]

            if module.tenant_id != tenant_id:
                raise KeyError("Module %u not in tenant %s" % (module_id,
                                                               tenant_id))

            self.server.remove_module(module_id)

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)
        self.set_status(204, None)


class Module(object):
    """Module object.

    Attributes:
        module_id: A progressive id unique within a given tenant (int)
        module_type: A system-wide unique name for the module
        worker: the module worker responsible for reating new module instances.
        tenant_id: The tenant's Id for convenience (UUID)
        every: loop period
        callback: Module callback (FunctionType)
    """

    REQUIRED = ['module_type', 'worker', 'tenant_id']

    def __init__(self):

        self.module_id = 0
        self.module_type = None
        self.worker = None
        self.__tenant_id = None
        self.__every = 5000
        self.__callback = None
        self.__worker = None
        self.log = empower.logger.get_logger()

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

            if isinstance(callback, types.FunctionType) or \
               isinstance(callback, types.MethodType):

                callback(serializable)

            elif isinstance(callback, list) and len(callback) == 2:

                exec_xmlrpc(callback, (as_json, ))

            else:

                raise TypeError("Invalid callback type")

        except Exception as ex:

            LOG.exception(ex)

    @property
    def tenant_id(self):
        """Return tenant id."""

        return self.__tenant_id

    @tenant_id.setter
    def tenant_id(self, value):
        """ Set tenant id."""

        self.__tenant_id = value

    @property
    def every(self):
        """Return every."""

        return self.__every

    @every.setter
    def every(self, value):
        """Set every."""

        self.__every = int(value)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = {'id': self.module_id,
               'module_type': self.module_type,
               'tenant_id': self.tenant_id,
               'every': self.every,
               'callback': self.callback}

        return out

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

        if isinstance(callback, types.FunctionType) or \
           isinstance(callback, types.MethodType):

            self.__callback = callback

        elif isinstance(callback, list) and len(callback) == 2:

            self.__callback = callback

        else:

            raise TypeError("Invalid callback type")

    def __str__(self):
        return "Module %u type %s" % (self.module_id, self.module_type)

    def __hash__(self):
        return hash(str(self.tenant_id) + str(self.module_id))

    def __eq__(self, other):

        if isinstance(other, Module):
            return self.module_type == other.module_type and \
                self.tenant_id == other.tenant_id and \
                self.every == other.every

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def start(self):
        """Start worker."""

        if self.every == -1:
            self.run_once()
        else:
            self.__worker = tornado.ioloop.PeriodicCallback(self.run_once,
                                                            self.every)
            self.__worker.start()

    def stop(self):
        """Stop worker."""

        self.__worker.stop()

    def run_once(self):
        """Period task."""

        pass

    def handle_response(self, response):
        """Stub handle response method."""

        pass


class ModuleWorker(object):
    """Module worker.

    Keeps track of the currently defined modules for each tenant

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    MODULE_NAME = None
    MODULE_TYPE = None

    def __init__(self, server, module, pt_type, pt_packet):

        self.__module_id = 0
        self.modules = {}
        self.pt_type = pt_type
        self.pt_packet = pt_packet
        self.module = module
        self.pnfp_server = RUNTIME.components[server]
        self.rest_server = RUNTIME.components[RESTServer.__module__]

        module_name = self.module.MODULE_NAME

        url = r"/api/v1/tenants/([a-zA-Z0-9:-]*)/%s/?"
        handler = (url % module_name, ModuleHandler, dict(server=self))
        self.rest_server.add_handler(handler)

        url = r"/api/v1/tenants/([a-zA-Z0-9:-]*)/%s/([0-9]*)/?"
        handler = (url % module_name, ModuleHandler, dict(server=self))
        self.rest_server.add_handler(handler)

        self.pnfp_server.register_message(self.pt_type, self.pt_packet,
                                          self.handle_packet)

    def remove_handlers(self):
        """Remove primitive handlers."""

        def determine(spec, regex, module_handler):
            """Match url."""

            if spec.handler_class == module_handler and spec.regex == regex:
                return False

            return True

        module_name = self.module.MODULE_NAME

        url = r"/api/v1/tenants/([a-zA-Z0-9:-]*)/%s/?$"
        regex = re.compile(url % module_name)
        for handler in self.rest_server.handlers:
            handler[1][:] = \
                [x for x in handler[1] if determine(x, regex, ModuleHandler)]

        url = r"/api/v1/tenants/([a-zA-Z0-9:-]*)/%s/([0-9]*)/?$"
        regex = re.compile(url % module_name)
        for handler in self.rest_server.handlers:
            handler[1][:] = \
                [x for x in handler[1] if determine(x, regex, ModuleHandler)]

    def handle_packet(self, response):
        """Handle response message."""

        if response.module_id not in self.modules:
            return

        module = self.modules[response.module_id]

        LOG.info("Received %s response (id=%u)", self.module.MODULE_NAME,
                 response.module_id)

        module.handle_response(response)

    @property
    def module_id(self):
        """Return new module id."""

        self.__module_id += 1
        return self.__module_id

    @module_id.setter
    def module_id(self, value):
        """Set the module id."""

        self.__module_id = value

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

        # check if tenant is available
        if module.tenant_id not in RUNTIME.tenants:
            raise KeyError("tenant %s not defined" % module.tenant_id)

        # check if an equivalent module has already been defined in the tenant
        for val in self.modules.values():
            # if so return a reference to that trigger
            if val == module:
                return val

        # otherwise generate a new module id
        module.module_id = self.module_id

        # set worker
        module.worker = self

        # start module
        module.start()

        # add to dict
        self.modules[module.module_id] = module
        return module

    def remove_module(self, module_id):
        """Remove a module.

        Args:
            tenant_id, the tenant id

        Returns:
            None

        Raises:
            KeyError, if tenant_id is not found
        """

        if module_id not in self.modules:
            return

        if self.modules[module_id].every >= 0:
            self.modules[module_id].stop()

        del self.modules[module_id]


class ModuleEventWorker(ModuleWorker):
    """Module event worker.

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def handle_packet(self, event):
        """Handle response message."""

        for module in self.modules.values():

            if module.tenant_id not in RUNTIME.tenants:
                continue

            LOG.info("New event %s: (id=%u)", self.module.MODULE_NAME,
                     module.module_id)

            module.handle_response(event)


class ModuleLVAPPWorker(ModuleWorker):
    """Module worker (LVAP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleWorker.__init__(self, LVAPPServer.__module__, module, pt_type,
                              pt_packet)


class ModuleLVNFPWorker(ModuleWorker):
    """Module worker (LVAP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleWorker.__init__(self, LVNFPServer.__module__, module, pt_type,
                              pt_packet)


class ModuleLVAPPEventWorker(ModuleEventWorker):
    """Module worker (LVAP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleEventWorker.__init__(self, LVAPPServer.__module__, module,
                                   pt_type, pt_packet)


class ModuleLVNFPEventWorker(ModuleEventWorker):
    """Module worker (LVAP Server version).

    Keeps track of the currently defined modules for each tenant (events only)

    Attributes:
        module_id: Next module id
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, module, pt_type, pt_packet=None):
        ModuleEventWorker.__init__(self, LVNFPServer.__module__, module,
                                   pt_type, pt_packet)
