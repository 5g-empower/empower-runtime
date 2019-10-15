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

"""Persistency manager."""

import ssl

from pymodm.connection import connect

from empower.core.service import EService

DEFAULT_URI = "mongodb://localhost:27017/empower"


class PersistencyManager(EService):
    """Persistency manager."""

    def __init__(self, context, service_id, uri):

        super().__init__(context=context, service_id=service_id, uri=uri)

    def start(self):
        """Start persistency manager."""

        super().start()

        connect(self.uri, ssl_cert_reqs=ssl.CERT_NONE)

        self.log.info("Connected to MongoDB: %s", self.uri)

    @property
    def uri(self):
        """Return uri."""

        return self.params["uri"]

    @uri.setter
    def uri(self, value):
        """Set uri."""

        self.params["uri"] = value


def launch(context, service_id, uri=DEFAULT_URI):
    """Start the persistency manager. """

    return PersistencyManager(context=context, service_id=service_id, uri=uri)
