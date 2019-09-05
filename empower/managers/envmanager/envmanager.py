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

"""Conf manager."""

import uuid

import empower.workers

from empower.core.service import EService

from empower.managers.envmanager.workershandler import WorkerAttributesHandler
from empower.managers.envmanager.workershandler import WorkersHandler
from empower.managers.envmanager.cataloghandler import CatalogHandler
from empower.managers.envmanager.envhandler import EnvHandler

from empower.managers.envmanager.env import Env


class EnvManager(EService):
    """Projects manager."""

    HANDLERS = [WorkersHandler, WorkerAttributesHandler, CatalogHandler,
                EnvHandler]

    env = None

    def start(self):
        """Start configuration manager."""

        super().start()

        if not Env.objects.all().count():
            Env(project_id=uuid.uuid4()).save()

        self.env = Env.objects.first()

        self.env.start_services()

    @property
    def catalog(self):
        """Return available workers."""

        return self.walk_module(empower.workers)


def launch(**kwargs):
    """Start project manager."""

    return EnvManager(**kwargs)
