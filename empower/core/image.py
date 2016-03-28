#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Image Class."""


class Image(object):
    """Image object representing a VNF template.

    Attributes:
        nb_ports: Number of ports (Integer)
        vnf: The virtual network function as a click script (str)
        handlers: the list of handlers supported by the vnf
        state_handlers: the list of state handlers supported by the vnf
    """

    def __init__(self, nb_ports, vnf, state_handlers, handlers):

        self.nb_ports = nb_ports
        self.vnf = vnf
        self.handlers = {}
        self.state_handlers = []
        self.add_handlers(handlers)
        self.add_state_handlers(state_handlers)

    def add_handlers(self, handlers):
        """add vnf-specifc handlers."""

        for handler in handlers:

            if isinstance(handler, list):
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

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Poll """

        return {'nb_ports': self.nb_ports,
                'vnf': self.vnf,
                'state_handlers': self.state_handlers,
                'handlers': [(k, v) for k, v in self.handlers.items()]}
