#!/usr/bin/env python3
#
# Copyright (c) 2019 Estefania Coronado
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

"""Simple app to test Wi-Fi events."""

from empower.managers.ranmanager.lvapp.wifiapp import EWiFiApp

from empower.core.app import EVERY


class WiFiEvents(EWiFiApp):
    """Simple app to test Wi-Fi events."""

    def handle_wtp_up(self, wtp):
        """Called when a WTP is up."""

        self.log.info("WTP %s UP!", wtp)

    def handle_wtp_down(self, wtp):
        """Called when a WTP is down."""

        self.log.info("WTP %s DOWN!", wtp)

    def handle_lvap_join(self, lvap):
        """Called when a LVAP joins the network."""

        self.log.info("LVAP %s joined %s!", lvap.addr,
                      self.context.wifi_props.ssid)

    def handle_lvap_leave(self, lvap):
        """Called when a LVAP leaves the network."""

        self.log.info("LVAP %s left %s!", lvap.addr,
                      self.context.wifi_props.ssid)


def launch(context, service_id, every=EVERY):
    """ Initialize the module. """

    return WiFiEvents(context=context, service_id=service_id, every=every)
