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

"""EmPOWER utils."""

import random


def get_module(module):
    """Get an empower module or return None."""

    from empower.main import RUNTIME

    if module not in RUNTIME.components:
        return None

    return RUNTIME.components[module]


def get_xid():
    """Return randon 32bits integers to be used as xid."""

    return random.getrandbits(32)
