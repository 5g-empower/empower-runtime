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

"""Alerts manager."""

import math

from empower_core.service import EService
from empower_core.etheraddress import EtherAddress

from empower.managers.alertsmanager.alert import Alert
from empower.managers.alertsmanager.alertshandler import AlertsHandler
from empower.managers.alertsmanager.alertssubscriptionshandler \
    import AlertsSubscriptionsHandler

WIFI_NWID_MAXSIZE = 32


class AlertsManager(EService):
    """Alerts manager."""

    HANDLERS = [AlertsHandler, AlertsSubscriptionsHandler]

    def __init__(self, context, service_id):

        super().__init__(context=context, service_id=service_id)

        self.alerts = {}
        self.message_id = 0

    def start(self):
        """Start api manager."""

        super().start()

        for alert in Alert.objects:
            self.alerts[alert.uuid] = alert

    def get_beacons(self, sta):
        """Get all the beacons for this station."""

        beacons = []

        for alert in self.alerts.values():

            subs = []

            if alert.subscriptions:
                for entry in alert.subscriptions.split(","):
                    subs.append(EtherAddress(entry))

            # sta not in subs, can ignore the alert
            #if sta not in subs:
            #    continue

            # start processing the alert
            message = "Questo e` un alert veramente molto lungo, deve essere" \
                      " diviso in due"

            nb_chunks = math.ceil(len(message) / 30)
            chunks = [message[i:i+30] for i in range(0, len(message), 30)]

            self.message_id = (self.message_id + 1) % 255
            msg_id = '{0:0{1}X}'.format(self.message_id, 2)

            chunk_id = 0

            for chunk in chunks:

                bytes_ssid = chunk.encode('UTF-8')
                bytes_ssid = bytes_ssid + b'\0' * \
                    (WIFI_NWID_MAXSIZE + 1 - len(bytes_ssid))

                if chunk_id == nb_chunks - 1:
                    bssid = "00:0D:B9:%s:%u:00" % (msg_id, chunk_id)
                else:
                    bssid = "00:0D:B9:%s:%u:01" % (msg_id, chunk_id)

                beacon = {
                    "dst": EtherAddress("FF:FF:FF:FF:FF:FF"),
                    "bssid": EtherAddress(bssid),
                    "ssid": bytes_ssid
                }

                beacons.append(beacon)

                chunk_id = chunk_id + 1

        return beacons

    def get_sub(self, uuid, sub=None):
        """Get subscription(s)."""

        alert = self.alerts[uuid]

        subs = []
        if alert.subscriptions:
            for entry in alert.subscriptions.split(","):
                subs.append(EtherAddress(entry))

        if not sub:
            return subs

        if sub in subs:
            return sub

        raise KeyError("Subscription %s not found" % sub)

    def add_sub(self, uuid, sub):
        """Add a new subscription."""

        alert = self.alerts[uuid]

        try:

            subs = set()
            if alert.subscriptions:
                for entry in alert.subscriptions.split(","):
                    subs.add(EtherAddress(entry))

            subs.add(sub)

            subs_string = []
            for entry in subs:
                subs_string.append(str(entry))

            alert.subscriptions = ",".join(subs_string)
            alert.save()

        finally:
            alert.refresh_from_db()

        return self.alerts[alert.uuid]

    def del_sub(self, uuid, sub):
        """Del a subscription."""

        alert = self.alerts[uuid]

        try:

            subs = set()
            if alert.subscriptions:
                for entry in alert.subscriptions.split(","):
                    subs.add(EtherAddress(entry))

            subs.remove(sub)

            subs_string = []
            for entry in subs:
                subs_string.append(str(entry))

            alert.subscriptions = ",".join(subs_string)
            alert.save()

        finally:
            alert.refresh_from_db()

        return self.alerts[alert.uuid]

    def create(self, uuid, alert="Generic alert"):
        """Create new alert."""

        if uuid in self.alerts:
            raise ValueError("Alert %s already defined" % uuid)

        alert = Alert(uuid=uuid, alert=alert)
        alert.save()

        self.alerts[alert.uuid] = alert

        return self.alerts[alert.uuid]

    def remove_all(self):
        """Remove all alerts."""

        for uuid in list(self.alerts):
            self.remove(uuid)

    def remove(self, uuid):
        """Remove alert."""

        if uuid not in self.alerts:
            raise KeyError("Alert %s not registered" % uuid)

        alert = self.alerts[uuid]

        alert.delete()

        del self.alerts[uuid]


def launch(context, service_id):
    """ Initialize the module. """

    return AlertsManager(context=context, service_id=service_id)
