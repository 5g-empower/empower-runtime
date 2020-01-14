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

"""Hello world app"""

from empower.core.app import EApp
from empower.core.app import EVERY


class HelloWorld(EApp):
    """Hello world app.

    This app simply prints to screen the message: "Hello! World."

    Parameters:
        service_id: the service id as an UUID (mandatory)
        project_id: the project id as an UUID (mandatory)
        message: the message to be printed (optional, default "World")
        every: the loop period in ms (optional, default 2000ms)

    Example:
        POST /api/v1/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26/apps
        {
            "name": "empower.apps.helloworld.helloworld",
            "params": {
                "message": "Bob",
                "every": 2000
            }
        }
    """

    def __eq__(self, other):
        if isinstance(other, HelloWorld):
            return self.message == other.message and self.every == other.every
        return False

    @property
    def message(self):
        """Return message."""

        return self.params["message"]

    @message.setter
    def message(self, value):
        """Set message."""

        self.params["message"] = value

    def loop(self):
        """Periodic job."""

        print("Hello! %s." % self.message)


def launch(context, service_id, message="World", every=EVERY):
    """ Initialize the module. """

    return HelloWorld(context=context, service_id=service_id,
                      message=message, every=every)
