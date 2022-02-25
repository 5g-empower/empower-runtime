#!/usr/bin/env python3
#
# Copyright (c) 2022 Roberto Riggio
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

"""Alert class."""

import logging

from pymodm import MongoModel, fields

from empower_core.serialize import serializable_dict
from empower_core.etheraddress import EtherAddress


@serializable_dict
class Alert(MongoModel):
    """Base Alert class.

    Attributes:
        uuid: This Device MAC address (EtherAddress)
        alert: A human-radable description of this Device (str)
        subscriptions: the list of MAC subscribed to this alert
        wtp: the list WTP that should broadcast this alert
        log: logging facility
    """

    alert_id = fields.UUIDField(primary_key=True)
    message = fields.CharField(required=True)
    subscriptions = fields.CharField(required=False)
    wtps = fields.CharField(required=False)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.log = logging.getLogger("%s" % self.__class__.__module__)

    def get_wtps(self):
        """Return wtps."""

        if self.wtps:
            return {EtherAddress(x) for x in self.wtps.split(",")}

        return set()

    def set_wtps(self, wtps):
        """Set wtps."""

        if not wtps:
            self.wtps = None
            return

        self.wtps = ",".join([str(x) for x in wtps])

        self.save()

    def get_subs(self):
        """Return subscriptions."""

        if self.subscriptions:
            return {EtherAddress(x) for x in self.subscriptions.split(",")}

        return set()

    def set_subs(self, subs):
        """Set subscriptions."""

        if not subs:
            self.subscriptions = None
            return

        self.subscriptions = ",".join([str(x) for x in subs])

        self.save()

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = {
            'alert_id': self.alert_id,
            'message': self.message,
            'subscriptions': self.get_subs()
        }

        return out

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "%s - %s" % (self.alert_id, self.message)

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.alert_id)

    def __eq__(self, other):
        if isinstance(other, Alert):
            return self.alert_id == other.alert_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"
