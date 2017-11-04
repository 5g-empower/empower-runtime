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

"""EmPOWER base service class."""

import time
import uuid
import tornado.ioloop
import empower.logger

from empower.main import RUNTIME

DEFAULT_PERIOD = 5000


class Service:
    """Service class.

    This is the basic service class. EmPOWER loosely follows the RFC7426.
    Services implements generics functions that offer open interfaces to other
    applications and services. Apps are a special class of services that do not
    offer interface to other services or app and that live only within a
    tenant. Services on the other hand live outside tenants.

    Attributes:
        every: the loop period
    """

    def __init__(self, **kwargs):

        self.__every = DEFAULT_PERIOD
        self.params = []
        self.log = empower.logger.get_logger()
        self.worker = None

        for param in kwargs:
            setattr(self, param, kwargs[param])
            self.params.append(param)

    def start(self):
        """Start control loop."""

        if self.every == -1:
            return

        self.worker = \
            tornado.ioloop.PeriodicCallback(self.loop, self.every)
        self.worker.start()

    def stop(self):
        """Stop control loop."""

        if self.every == -1:
            return

        self.worker.stop()

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        params = {}
        params['every'] = self.every
        params['params'] = self.params

        for param in self.params:
            params[param] = getattr(self, param)

        return params

    def loop(self):
        """Control loop."""

        pass
