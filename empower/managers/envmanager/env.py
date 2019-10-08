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

"""Runtime configuration."""

import uuid

from importlib import import_module
from pymodm import MongoModel, fields

import empower.core.serialize as serialize

from empower.main import srv_or_die


class Env(MongoModel):
    """Env class

    Attributes:
        project_id: The project identifier. Notice how there is only one Env
            instance active at any given time and that the project_id of the
            workers loaded by Env is always set to the Env's project_id
        bootstrap: the list of services to be loaded at bootstrap with their
            configuration
        storage: the configuration of the services
        services: the services
    """

    project_id = fields.UUIDField(primary_key=True)
    bootstrap = fields.DictField(required=False, blank=True)
    storage = fields.DictField(required=False, blank=True)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.services = {}

        # Save pointer to LVAPPManager
        self.lvapp_manager = \
            srv_or_die("empower.managers.ranmanager.lvapp.lvappmanager")

        # Save pointer to VBSPManager
        self.vbsp_manager = \
            srv_or_die("empower.managers.ranmanager.vbsp.vbspmanager")

        # Save pointer to TimeSeriesManaget
        self.ts_manager = \
            srv_or_die("empower.managers.timeseriesmanager.timeseriesmanager")

        # Save pointer to ApiManager
        self.api_manager = srv_or_die("empower.managers.apimanager.apimanager")

    def get_service(self, name, **kwargs):
        """Get a service.

        Return a service with the same name and parameters if already running
        or start a new one."""

        if not kwargs:
            kwargs = {}

        kwargs['service_id'] = uuid.uuid4()
        kwargs['project_id'] = self.project_id

        init_method = getattr(import_module(name), "launch")
        requested = init_method(**kwargs)

        for service in self.services.values():
            if service == requested:
                return service

        service = self.register_service(service_id=uuid.uuid4(), name=name,
                                        params=kwargs)

        return service

    def save_service_state(self, service_id):
        """Save service state."""

        service = self.services[service_id]

        self.bootstrap[str(service.service_id)] = {
            "name": service.name,
            "params": serialize.serialize(service.params)
        }

        self.storage[str(service.service_id)] = \
            serialize.serialize(service.storage)

        self.save()

    def register_service(self, service_id, name, params):
        """Register service."""

        if service_id in self.services:
            raise ValueError("Service %s already registered" % service_id)

        params['service_id'] = service_id
        params['project_id'] = self.project_id

        storage = {}

        self.start_service(service_id, name, params, storage)
        self.save_service_state(service_id)

        return self.services[service_id]

    def unregister_service(self, service_id):
        """Unregister service."""

        if service_id not in self.services:
            raise ValueError("Service %s not registered" % service_id)

        self.stop_service(service_id)

        del self.bootstrap[str(service_id)]
        del self.storage[str(service_id)]

        self.save()

    def reconfigure_service(self, service_id, params):
        """Reconfigure service."""

        if service_id not in self.services:
            raise ValueError("Service %s not registered" % service_id)

        service = self.services[service_id]

        for param in params:

            if param not in self.bootstrap[str(service_id)]['params']:
                raise KeyError("Param %s undefined" % param)

            setattr(service, param, params[param])

        self.save_service_state(service_id)

        return self.services[service_id]

    def start_services(self):
        """Start registered services."""

        for service_id in self.bootstrap:
            name = self.bootstrap[service_id]['name']
            params = self.bootstrap[service_id]['params']
            storage = self.storage[service_id]
            self.start_service(uuid.UUID(service_id), name, params, storage)

    def stop_services(self):
        """Stop registered services."""

        for service_id in self.bootstrap:
            self.stop_service(uuid.UUID(service_id))

    def start_service(self, service_id, name, params, storage):
        """Start a service."""

        if service_id in self.services:
            raise ValueError("Service %s is already running" % service_id)

        # this will look for the launch method and call it
        init_method = getattr(import_module(name), "launch")
        service = init_method(**params)

        # set context
        service.context = self

        # set storage
        service.set_storage(storage)

        # register handlers
        for handler in service.HANDLERS:
            self.api_manager.register_handler(handler)
            handler.service = service

        # start service
        service.start()

        self.services[service_id] = service

        return service

    def stop_service(self, service_id):
        """Stop a service."""

        if service_id not in self.services:
            raise ValueError("Service %s not running" % service_id)

        self.services[service_id].stop()
        del self.services[service_id]

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = {}

        output['project_id'] = self.project_id
        output['bootstrap'] = self.bootstrap

        return output

    def to_str(self):
        """Return an ASCII representation of the object."""

        return str(self.project_id)

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.project_id)

    def __eq__(self, other):
        if isinstance(other, Env):
            return self.project_id == other.project_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
