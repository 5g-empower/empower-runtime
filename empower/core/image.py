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

"""Image Class."""

DEFAULT_HANDLERS = [["config", "config"],
                    ["handlers", "handlers"]]


class Image(object):
    """Image object representing a VNF template.

    Attributes:
        nb_ports: Number of ports (Integer)
        vnf: The virtual network function as a click script (str)
        handlers: the list of handlers supported by the vnf
        state_handlers: the list of state handlers supported by the vnf
    """

    def __init__(self, vnf, nb_ports=1, state_handlers=[], handlers=[]):

        self.nb_ports = nb_ports
        self.vnf = vnf
        self.handlers = {}
        self.state_handlers = []
        self.add_handlers(handlers)
        self.add_handlers(DEFAULT_HANDLERS)
        self.add_state_handlers(state_handlers)

    def add_handlers(self, handlers):
        """add vnf-specifc handlers."""

        for handler in handlers:

            if not isinstance(handler, list):
                raise ValueError("list expected")

            if len(handler) != 2:
                raise ValueError("list of length 2 expected")

            self.handlers[handler[0]] = handler[1]

    def add_state_handlers(self, state_handlers):
        """Add state handlers."""

        for state_handler in state_handlers:

            if state_handler not in self.handlers:
                raise KeyError("state handler %s not found" % state_handler)

            self.state_handlers.append(state_handler)

    def __eq__(self, other):
        if isinstance(other, Image):
            return self.vnf == other.vnf
        return False

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Poll """

        return {'nb_ports': self.nb_ports,
                'vnf': self.vnf,
                'state_handlers': self.state_handlers,
                'handlers': [(k, v) for k, v in self.handlers.items()]}
