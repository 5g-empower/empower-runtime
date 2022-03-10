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

"""Alerts manager."""

import math

from empower_core.service import EService
from empower_core.etheraddress import EtherAddress
from empower_core.ssid import WIFI_NWID_MAXSIZE

from empower.managers.alertsmanager.alert import Alert
from empower.managers.alertsmanager.alertshandler import AlertsHandler
from empower.managers.alertsmanager.alertssubscriptionshandler \
    import AlertsSubscriptionsHandler
from empower.managers.alertsmanager.alertswtpshandler import AlertsWTPsHandler


class AlertsManager(EService):
    """Alerts manager."""

    HANDLERS = [AlertsHandler, AlertsSubscriptionsHandler, AlertsWTPsHandler]

    def __init__(self, context, service_id):

        super().__init__(context=context, service_id=service_id)

        self.alerts = {}
        self.message_id = 0

    def start(self):
        """Start api manager."""

        super().start()

        for alert in Alert.objects:
            self.alerts[alert.alert_id] = alert

    def get_beacons(self, sta, wtp):
        """Get all the beacons for this station."""

        beacons = []

        for alert in self.alerts.values():

            # wtp not in alert
            if wtp not in alert.get_wtps():
                continue

            # sta not in subs, can ignore the alert
            #if sta not in alert.get_subs():
            #    continue

            # start processing the alert
            message = alert.message

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

    def add_sub(self, alert_id, sub):
        """Add a new subscription."""

        alert = self.alerts[alert_id]

        try:
            subs = alert.get_subs()
            subs.add(sub)
            alert.set_subs(subs)
        finally:
            alert.refresh_from_db()

        return self.alerts[alert.alert_id]

    def del_sub(self, alert_id, sub):
        """Del a subscription."""

        alert = self.alerts[alert_id]

        try:
            subs = alert.get_subs()
            subs.remove(sub)
            alert.set_subs(subs)
        finally:
            alert.refresh_from_db()

        return self.alerts[alert.alert_id]

    def add_wtp(self, alert_id, wtp):
        """Add a new wtp."""

        alert = self.alerts[alert_id]

        try:
            wtps = alert.get_wtps()
            wtps.add(wtp)
            alert.set_wtps(wtps)
        finally:
            alert.refresh_from_db()

        return self.alerts[alert.alert_id]

    def del_wtp(self, alert_id, wtp):
        """Del a wtp."""

        alert = self.alerts[alert_id]

        try:
            wtps = alert.get_wtps()
            wtps.remove(wtp)
            alert.set_wtps(wtps)
        finally:
            alert.refresh_from_db()

        return self.alerts[alert.alert_id]

    def create(self, alert_id, message="Generic alert"):
        """Create new alert."""

        if alert_id in self.alerts:
            raise ValueError("Alert %s already defined" % alert_id)

        alert = Alert(alert_id=alert_id, message=message)
        alert.save()

        self.alerts[alert.alert_id] = alert

        return self.alerts[alert.alert_id]

    def update(self, alert_id, message):
        """Create new alert."""

        alert = self.alerts[alert_id]

        try:
            alert.message = message
            alert.save()
        finally:
            alert.refresh_from_db()

        return self.alerts[alert.alert_id]

    def remove_all(self):
        """Remove all alerts."""

        for alert_id in list(self.alerts):
            self.remove(alert_id)

    def remove(self, alert_id):
        """Remove alert."""

        if alert_id not in self.alerts:
            raise KeyError("Alert %s not registered" % alert_id)

        alert = self.alerts[alert_id]

        alert.delete()

        del self.alerts[alert_id]


def launch(context, service_id):
    """ Initialize the module. """

    return AlertsManager(context=context, service_id=service_id)
