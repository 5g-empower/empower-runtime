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

import tornado.web
import tornado.httpserver

from empower.core.service import ServiceWorker
from empower.core.service import Service

from empower.main import RUNTIME


class Module(Service):
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

        super().__init__()

        self.__tenant_id = None

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


class ModuleWorker(ServiceWorker):
    """Module worker.

    Keeps track of the currently defined modules for each tenant

    Attributes:
        modules: dictionary of modules currently active in this tenant
    """

    def __init__(self, server, module, pt_type, pt_packet):

        super().__init__(server, pt_type, pt_packet)

        self.__module_id = 0
        self.modules = {}
        self.module = module

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
