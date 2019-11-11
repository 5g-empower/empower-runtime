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

import uuid
import pkgutil
import logging

import tornado.ioloop

from empower.core.serialize import serializable_dict


@serializable_dict
class EService:
    """Base service class."""

    HANDLERS = []

    def __init__(self, context, service_id, **kwargs):

        # Declaration
        self._service_id = None

        # Pointer to an Env or a Project object (can be None)
        self.context = context

        # Set the service id
        self.service_id = service_id

        # If every is not specified then disable periodic loop
        if 'every' not in kwargs:
            kwargs['every'] = -1

        # Service's callbacks
        self.callbacks = set()

        # Human readable name
        self.name = "%s" % self.__class__.__module__

        # Set logger
        self.log = logging.getLogger(self.name)

        # Worker process, set only if every > 0
        self.worker = None

        # Persistent dict
        self.storage = {}

        # Service parameters
        self.params = {}

        # Set service parameters
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def set_storage(self, storage=None):
        """Set persistent attributes."""

        if not storage:
            return

        for attribute in storage:
            setattr(self, attribute, storage[attribute])

    def save_service_state(self):
        """Save service state."""

        if not self.context:
            return

        self.context.save_service_state(self.service_id)

    def register_service(self, name, **kwargs):
        """Get a service.

        Return a service with the same name and parameters if already running
        or start a new one."""

        if not self.context:
            return None

        return self.context.register_service(name, **kwargs)

    def handle_callbacks(self):
        """Invoke registered callbacks."""

        for callback in self.callbacks:
            callback(self)

    def add_callback(self, method):
        """Add a new callback."""

        self.callbacks.add(method)

    def remove_callback(self, method):
        """Remove a callback."""

        self.callbacks.remove(method)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = {}

        output['service_id'] = self.service_id
        output['name'] = self.name
        output['params'] = self.params

        if self.context:
            output['project_id'] = self.context.project_id

        return output

    @property
    def service_id(self):
        """Get service_id."""

        return self._service_id

    @service_id.setter
    def service_id(self, value):
        """Set service_id."""

        if isinstance(value, uuid.UUID):
            self._service_id = value
        else:
            self._service_id = uuid.UUID(value)

    @property
    def every(self):
        """Return loop period."""

        return self.params["every"]

    @every.setter
    def every(self, value):
        """Set loop period."""

        self.params["every"] = int(value)

        if self.worker:
            self.stop()
            self.start()

    def write_points(self, points):
        """Write points to InfluxDB."""

        self.context.ts_manager.write_points(points)

    def start(self):
        """Start control loop."""

        # Not supposed to run a loop
        if self.every == -1:
            return

        # Start the control loop
        self.worker = \
            tornado.ioloop.PeriodicCallback(self.loop, self.every)

        self.worker.start()

    def stop(self):
        """Stop control loop."""

        # save state
        self.save_service_state()

        # Not supposed to run a loop
        if self.every == -1:
            return

        # stop the control loop
        self.worker.stop()
        self.worker = None

    def loop(self):
        """Control loop."""

        self.log.info("Empty loop")

    @classmethod
    def walk_module(cls, package):
        """Inspect the specified module for services."""

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

            if 'name' not in manifest:
                manifest['name'] = module_name

            if 'desc' not in manifest:
                manifest['desc'] = "No description available"

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
            return self.name == other.name and self.every == other.every
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
