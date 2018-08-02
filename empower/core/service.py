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

"""EmPOWER base service class."""

import json
import types
import xmlrpc.client

from multiprocessing.pool import ThreadPool
from tornado.ioloop import IOLoop

import empower.logger

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


class Service:
    """Service object.

    Attributes:
        module_id: The module identifier. Unique for a given module_type.
        module_type: A system-wide unique name for the module
        worker: the module worker responsible for reating new module instances.
        callback: Module callback (FunctionType)
    """

    MODULE_NAME = None
    REQUIRED = ['module_type', 'worker']

    def __init__(self):

        self.module_id = 0
        self.module_type = None
        self.worker = None
        self.__callback = None
        self.__periodic = None
        self.log = empower.logger.get_logger()

    def unload(self):
        """Remove this module."""

        self.worker.remove_module(self.module_id)

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

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = {'id': self.module_id,
               'module_type': self.module_type,
               'callback': self.callback}

        return out

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

    def __str__(self):
        return "Module %u type %s" % (self.module_id, self.module_type)

    def __hash__(self):
        return hash(str(self.module_id))

    def __eq__(self, other):

        if isinstance(other, Service):
            return self.module_type == other.module_type

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

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


class ServiceWorker:
    """Service class.

    This is the basic service class. EmPOWER loosely follows the RFC7426.
    Services implements generics functions that offer open interfaces to other
    applications and services. Apps are a special class of services that do not
    offer interface to other services or app and that live only within a
    tenant. Services on the other hand live outside tenants.

    Attributes:
        every: the loop period
    """

    def __init__(self, server, pt_type, pt_packet):

        self.pt_type = pt_type
        self.pt_packet = pt_packet
        self.pnfp_server = RUNTIME.components[server]

        self.pnfp_server.register_message(self.pt_type,
                                          self.pt_packet,
                                          self.handle_packet)

        self.log = empower.logger.get_logger()

    def handle_packet(self, pnfdev, message):
        """Handle response message."""

        pass
