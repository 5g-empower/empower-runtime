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

"""Application."""

from empower.core.service import EService

EVERY = 2000


class EApp(EService):
    """Base app class."""

    MODULES = []

    def __init__(self, context, **kwargs):

        super().__init__(context=context, **kwargs)

    def start(self):
        """Start app."""

        for module in self.MODULES:
            module.register_callbacks(self)

        # start the app
        super().start()

    def stop(self):
        """Stop app."""

        for module in self.MODULES:
            module.unregister_callbacks(self)

        # stop the app
        super().stop()
