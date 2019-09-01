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

"""Base service class."""

import pkgutil
import uuid
import logging
import tornado.ioloop

from empower.main import srv_or_die


class EService:
    """Base service class."""

    HANDLERS = []

    def __init__(self, service_id, project_id, **kwargs):

        kwargs['service_id'] = service_id
        kwargs['project_id'] = project_id

        if 'every' not in kwargs:
            kwargs['every'] = -1

        # Service's callbacks. Invoke the method 'handle_callbacks' passing as
        # single parameter the name of an attribute that was just modified in
        # order to have all the registered callbacks invoked with the value of
        # the attribute passed as parameter
        self.callbacks = {}

        # Human readable name
        self.name = "%s" % self.__class__.__module__

        # Set logger
        self.log = logging.getLogger(self.name)

        # Worker process, set only if every > 0
        self.worker = None

        # Pointer to an Env or a Project object (can be null)
        self.context = None

        # List of attributes to be saved (only if a context is set)
        self.to_storage = []

        # Service parameters
        self.params = {}

        for param in kwargs:
            self.params[param] = None
            setattr(self, param, kwargs[param])

    def handle_callbacks(self, name):
        """Invoke all the callback registered on a given attrbute."""

        if name not in self.callbacks:
            return

        if not hasattr(self, name):
            return

        for callback in self.callbacks[name]:
            value = getattr(self, name)
            callback(value)

    def load(self):
        """Load configuration from storage."""

        if not self.context:
            return

        if str(self.service_id) not in self.context.storage:
            self.context.storage[str(self.service_id)] = {}

        storage = self.context.storage[str(self.service_id)]

        for attribute in self.to_storage:
            if attribute in storage and hasattr(self, attribute):
                setattr(self, attribute, storage[attribute])

    def save(self):
        """Save configuration to storage."""

        if not self.context:
            return

        if str(self.service_id) not in self.context.storage:
            self.context.storage[str(self.service_id)] = {}

        storage = self.context.storage[str(self.service_id)]

        for attribute in self.to_storage:
            if hasattr(self, attribute):
                storage[attribute] = getattr(self, attribute)

        self.context.save()

    def add_callback(self, attribute, method):
        """Add a new callback."""

        if attribute not in self.callbacks:
            self.callbacks[attribute] = set()

        self.callbacks[attribute].add(method)

    def remove_callback(self, attribute, method):
        """Add a new callback."""

        if attribute not in self.callbacks:
            return

        self.callbacks[attribute].remove(method)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = {}

        output['name'] = self.name
        output['params'] = self.params

        return output

    @property
    def project_id(self):
        """Return project_id."""

        return self.params["project_id"]

    @project_id.setter
    def project_id(self, value):
        """Set project_id."""

        if "project_id" in self.params and self.params["project_id"]:
            raise ValueError("Param project_id can not be changed")

        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)

        self.params["project_id"] = value

    @property
    def service_id(self):
        """Return service_id."""

        return self.params["service_id"]

    @service_id.setter
    def service_id(self, value):
        """Set service_id."""

        if "service_id" in self.params and self.params["service_id"]:
            raise ValueError("Param service_id can not be changed")

        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)

        self.params["service_id"] = value

    @property
    def every(self):
        """Return loop period."""

        return self.params["every"]

    @every.setter
    def every(self, value):
        """Set loop period."""

        self.params["every"] = int(value)

        if not self.worker:
            return

        self.worker.stop()

        self.worker = \
            tornado.ioloop.PeriodicCallback(self.loop, self.every)

        self.worker.start()

    def start(self, load):
        """Start control loop."""

        # Register handlers for this services
        api_manager = srv_or_die("empower.managers.apimanager.apimanager")
        for handler in self.HANDLERS:
            api_manager.register_handler(handler)

        # Set pointer to this service
        for handler in self.HANDLERS:
            handler.service = self

        # load configuration from database
        if load:
            self.load()

        # Not supposed to run a loop
        if self.every == -1:
            return

        # Start the control loop
        self.worker = \
            tornado.ioloop.PeriodicCallback(self.loop, self.every)

        self.worker.start()

    def stop(self, save):
        """Stop control loop."""

        # save configuration to database
        if save:
            self.save()

        # Not supposed to run a loop
        if self.every == -1:
            return

        # stop the control loop
        self.worker.stop()

    def loop(self):
        """Control loop."""

        self.log.info("Empty loop")

    @classmethod
    def walk_module(cls, package):
        """Inspect the specified module for 5G-EmPOWER services."""

        results = {}

        pkgs = pkgutil.walk_packages(package.__path__)

        for _, module_name, is_pkg in pkgs:

            __import__(package.__name__ + "." + module_name)

            if not is_pkg:
                continue

            if not hasattr(package, module_name):
                continue

            module = getattr(package, module_name)

            if not hasattr(module, "MANIFEST"):
                continue

            manifest = getattr(module, "MANIFEST")

            name = package.__name__ + "." + module_name + "." + module_name

            manifest['name'] = name
            manifest['desc'] = module.__doc__

            results[name] = manifest

        return results

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "%s" % self.name

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, EService):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
