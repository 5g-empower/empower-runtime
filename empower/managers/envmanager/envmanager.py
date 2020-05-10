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

from empower_core.envmanager.envmanager import EnvManager
from empower_core.walkmodule import walk_module

import empower.workers

from empower.managers.envmanager.env import EmpowerEnv


class EmpowerEnvManager(EnvManager):
    """Environment manager."""

    ENV_IMPL = EmpowerEnv

    @property
    def catalog(self):
        """Return available workers."""

        return walk_module(empower.workers)


def launch(context, service_id):
    """ Initialize the module. """

    return EmpowerEnvManager(context=context, service_id=service_id)
