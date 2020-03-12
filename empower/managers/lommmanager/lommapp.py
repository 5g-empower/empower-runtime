#!/usr/bin/env python3
#
# Copyright (c) 2020 Fondazione Bruno Kessler
# Author(s): Cristina Costa (ccosta@fbk.eu)
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
"""LoMM Test App."""

from empower.core.app import EApp

import empower.managers.lommmanager.lnsp as lnsp

from empower.core.launcher import srv_or_die

EVERY = 2000


class LoMMApp(EApp):
    """LoMM Basic App.

    Attributes:
        context (Project): Project context in which the app
                           is running (context.services)
        lgtws (dict): Registered LoRaWAN GTWs
        lenddevs (dict): Registered End Devices
        lnss (dict): Registered LNSs

    Avaliable LoMM lnsp callbacks:
        LoRaWAN GTW Events Callbacks:
            callback_new_state_transition: called when a GTW changes its state

        Uplink Web Socket Messages Callbacks:
            callback_version: called when a new Version msg. arrives
            callback_jreq: called when a new JREQ Frame arrives
            callback_updf: called when a new Uplink Data Frame arrives
            callback_propdf: called when a new Proprietary Frame arrives
            callback_dntxed: called when a new Trx. Confirmation msg. arrives
            callback_timesync: called when a new Timesync msg. arrives
            callback_rmtsh: called when a new remote shell msg. arrives

        Downlink Web Socket Messages Callbacks:
            callback_router_config: called when a new remote shell msg. is sent
            callback_dnmsg: called when a new dl frame msg. is sent
            callback_dnsched: called when a new dl scheduled frame msg. is sent
            callback_dn_timesync: called when a new timesync msg. is sent
            callback_rmcmd: called when a new remote command msg. is sent
            callback_dn_rmtsh: called when a new remote shell msg. is sent

        Monitoring Round-trip Times Callbacks:
            callback_rtt_data_rx: called when new RTT data is avaliable
            callback_rtt_query: called when a new RTT query is sent
            callback_rtt_on: called when RTT query is set to ON
            callback_rtt_off: called when RTT query is set to OFF

        Gathering Radio Data Statistics Callbacks:
            callback_new_radio_data: called when a lGTW radio data is avaliable
    """

    MODULES = [lnsp]

    @property
    def lgtws(self):
        """Return lGTWs registered in this project context."""
        lnsp_manager = srv_or_die("lnspmanager")
        return lnsp_manager.lgtws

    @property
    def lenddevs(self):
        """Return lEndDevs registered in this project context."""
        lnsp_manager = srv_or_die("lnspmanager")
        return lnsp_manager.lenddevs

    @property
    def lnss(self):
        """Return LNSs registered in this project context."""
        lnspd_manager = srv_or_die("lnspdmanager")
        return lnspd_manager.lnss
