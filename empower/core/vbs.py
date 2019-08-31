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

"""Virtual Base Station."""

from empower.core.device import Device


class VBS(Device):
    """Virtual Base Station.

    Attributes:
        cells: the cells supported by the VBS
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cells = {}

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = super().to_dict()
        out['cells'] = self.cells
        return out
