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

from empower_core.launcher import srv_or_die
from empower_core.serialize import serializable_dict
from empower_core.envmanager.env import Env


@serializable_dict
class EmpowerEnv(Env):
    """Empower Env class"""

    @property
    def wtps(self):
        """Return the WTPs."""

        return srv_or_die("lvappmanager").devices

    @property
    def vbses(self):
        """Return the VBSes."""

        return srv_or_die("vbspmanager").devices
