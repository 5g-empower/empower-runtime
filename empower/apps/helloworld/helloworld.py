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

"""Hello Manager App."""

from empower.core.app import EmpowerApp


class HelloWorld(EmpowerApp):
    """HelloWorld App.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.helloworld.helloworld \
            --tenant_id=52313ecb-9d00-4b7d-b873-b55d3d9ada26D
    """

    def loop(self):
        """Periodic job."""

        print("Hello! %s." % self.message)

    @property
    def message(self):
        """Return message."""

        return self.__message

    @message.setter
    def message(self, value):
        """Set message."""

        self.__message = value


def launch(tenant_id, message="World", every=5000):
    return HelloWorld(tenant_id=tenant_id, message=message, every=every)
