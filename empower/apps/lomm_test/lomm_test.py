#!/usr/bin/env python3
#
# Copyright (c) 2020 Cristina Costa
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
"""LoMM Test App for Empower.

The lomm_test application prints on screen data upon LoMM events:
    - LoRaWAN GTW Events:
        new_state_transition
    - Uplink Web Socket Messages Events:
        version, jreq, updf, propdf, dntxed, timesync, rmtsh
    - Downlink Web Socket Messages Events:
        router_config, dnmsg, dnsched, dn_timesync, rmcmd, dn_rmtsh
    - Monitoring Round-trip Times Events:
        rtt_data_rx, rtt_query, rtt_on, rtt_off
    - Gathering Radio Data Statistics Events:
        new_radio_data
"""

import json

from empower.managers.lommmanager.lommapp import LoMMApp


class LoMMTest(LoMMApp):
    """LoMMTest App. The LoMM Test App, prints LoMM events data on screen.

    Attributes:
        context (Project): Project context in which the app
                           is running (context.services)
        lgtws (dict): Registered LoRaWAN GTWs
        lenddevs (dict): Registered End Devices
        lnss (dict): Registered LNSs
        label (str): Application label (used in the log entries)

    Implemented callbacks:
        LoRaWAN GTW Events Callbacks:
            callback_new_state_transition: called when a GTW changes its state

        Uplink Web Socket Messages Callbacks:
            callback_version: called when a new Version message arrives
            callback_jreq: called when a new JREQ Frame arrives
            callback_updf: called when a new Uplink Data Frame arrives
            callback_propdf: called when a new Proprietary Frame arrives
            callback_dntxed: called when a new Transmit Confirmation
                             message arrives
            callback_timesync: called when a new Timesync message arrives
            callback_rmtsh: called when a new remote shell message arrives

        Downlink Web Socket Messages Callbacks:
            callback_router_config: called when a new remote shell
                                    message is sent
            callback_dnmsg: called when a new downlink frame message is sent
            callback_dnsched: called when a new downlink scheduled
                              frame message is sent
            callback_dn_timesync: called when a new timesync message is sent
            callback_rmcmd: called when a new remote command message is sent
            callback_dn_rmtsh: called when a new remote shell message is sent

        Monitoring Round-trip Times Callbacks:
            callback_rtt_data_rx: called when new RTT data is avaliable
            callback_rtt_query: called when a new RTT query is sent
            callback_rtt_on: called when RTT query is set to ON
            callback_rtt_off: called when RTT query is set to OFF

        Gathering Radio Data Statistics Callbacks:
            callback_new_radio_data: called when a LoRaWAN Radio GTW
            radio data is avaliable
    """

    # LoRaWAN GTW Events Callback
    def callback_new_state_transition(self, **kwargs):
        """Print log info when a GTW changes its state.

        Parameters:
            lgtw_id (UID): LoRaWAN GTW ID
            old_state ("disconnected", "connected", "online"):
            previous state of the GTW
            new_state ("disconnected", "connected", "online"):
            new state of the GTW
        """
        lgtw_id = kwargs.get("lgtw_id", "")
        old_state = kwargs.get("old_state", "")
        new_state = kwargs.get("new_state", "")

        self.log.info(
            "%s: lgtw %s transition frm %s to %s!",
            self.label, lgtw_id, old_state, new_state)

    # Uplink Web Socket Messages Callbacks
    def callback_version(self,  **kwargs):
        """Print log info when a new Version message arrives."""
        lgtw_id = kwargs.get("lgtw_id", "")
        rx_time = kwargs.get("rx_time", 0)
        lgtw_version = kwargs.get("lgtw_version", "")

        self.log.info(
            "%s: lGTW %s, version request received (%d)",
            self.label, lgtw_id, rx_time)
        self.log.info("%s: \n%s", self.label, json.dumps(lgtw_version))

    def callback_jreq(self,  **kwargs):
        """Print log info when a new JREQ Frame arrives."""
        lgtw_id = kwargs.get("lgtw_id", "")
        rx_time = kwargs.get("rx_time", 0)
        join_data = kwargs.get("join_data", "")
        xtime = kwargs.get("xtime", 0)
        rctx = kwargs.get("rctx", 0)
        phypayload = kwargs.get("PhyPayload", "")

        self.log.info(
            "%s: lGTW %s, join request frame received (%d)",
            self.label, lgtw_id, rx_time)
        self.log.info("%s: PhyPayload: %s ", self.label, phypayload)
        self.log.info("%s: xtime=%d, rctx=%d", self.label, xtime, rctx)
        self.log.info(
            "%s: \n%s", self.label,
            json.dumps(join_data, indent=2, sort_keys=True))

    def callback_updf(self,  **kwargs):
        """Print log info when a new Uplink Data Frame arrives."""
        lgtw_id = kwargs.get("lgtw_id", "")
        rx_time = kwargs.get("rx_time", 0)
        updf_data = kwargs.get("updf_data", "")
        xtime = kwargs.get("xtime", 0)
        rctx = kwargs.get("rctx", 0)
        phypayload = kwargs.get("PhyPayload", "")

        self.log.info(
            "%s: lGTW %s, uplink frame frame received (%d)",
            self.label, lgtw_id, rx_time)
        self.log.info("%s: PhyPayload: %s ", self.label, phypayload)
        self.log.info("%s: xtime=%d, rctx=%d", self.label, xtime, rctx)
        self.log.info(
            "%s: \n%s", self.label,
            json.dumps(updf_data, indent=2, sort_keys=True))

    def callback_propdf(self,  **kwargs):
        """Print log info when a new Proprietary Frame arrives."""
        lgtw_id = kwargs.get("lgtw_id", "")
        rx_time = kwargs.get("rx_time", 0)
        frmpayload = kwargs.get("FRMPayload", "")
        xtime = kwargs.get("xtime", 0)
        rctx = kwargs.get("rctx", 0)

        self.log.info(
            "%s: lGTW %s, proprietary frame received (%d)",
            self.label, lgtw_id, rx_time)
        self.log.info("%s: xtime=%d, rctx=%d", self.label, xtime, rctx)
        self.log.info("%s: frmpayload=%s", self.label, frmpayload)

    def callback_dntxed(self, **kwargs):
        """Print log info when a new Transmit Confirmation message arrives.

        This method is called when a frame has been put on air.
        There is no feedback to the LNS if a frame could not be sent
        """
        lgtw_id = kwargs.get("lgtw_id", "")
        rx_time = kwargs.get("rx_time", 0)
        dntxed = kwargs.get("dntxed", "")

        self.log.info(
            "%s: lGTW %s, packet transmission confirmation received (%d)",
            self.label, lgtw_id, rx_time)
        self.log.info(
            "%s: xtime=%d, rctx=%d",
            self.label, dntxed["xtime"], dntxed["rctx"])
        self.log.info(
            "%s: \n%s",
            self.label, json.dumps(dntxed, indent=2, sort_keys=True))

    def callback_timesync(self,  **kwargs):
        """Print log info when a new Timesync message arrives."""
        lgtw_id = kwargs.get("lgtw_id", "")
        # rx_time = kwargs.get("rx_time", 0)

        if "gpstime" in kwargs:
            self.log.info(
                "%s: lGTW %s, Transferring GPS Time (timesync) " +
                "message received (gpstime=%d, xtime=%d)",
                self.label, lgtw_id, kwargs["gpstime"], kwargs["xtime"])
        else:
            self.log.info(
                "%s: lGTW %s, GPS Time syncronization (timesync) " +
                "message received (txtime=%d)",
                self.label, lgtw_id, kwargs["txtime"])

    def callback_rmtsh(self,  **kwargs):
        """Print log info when a new remote shell message arrives."""
        lgtw_id = kwargs.get("lgtw_id", "")
        # rx_time = kwargs.get("rx_time", 0)
        rmtsh = kwargs.get("rmtsh", "")

        self.log.info(
            "%s: lGTW %s, current remote shell sessions state " +
            "received ", self.label, lgtw_id)

        for session in rmtsh:
            if rmtsh["started"]:
                self.log.info(
                  "%s: session pid = %d (running), user %s, %d secs " +
                  "since the input/output action", self.label,
                  session["pid"], session["user"], session["age"])
            else:
                self.log.info(
                    "%s: session pid = %d, user %s, %d secs since" +
                    " the input/output action", self.label,
                    session["pid"], session["user"], session["age"])

    """
    Downlink Web Socket Messages
    """
    def callback_router_config(self,  **kwargs):
        """Print log info when a new remote shell message is sent."""
        lgtw_id = kwargs.get("lgtw_id", "")
        tx_time = kwargs.get("tx_time", "")
        router_config = kwargs.get("msg", "")

        self.log.info(
            "%s: lGTW %s, lGTW configuration sent. (%d)",
            self.label, lgtw_id, tx_time)
        self.log.info(
            "%s: \n%s", self.label,
            json.dumps(router_config, indent=2, sort_keys=True))

    def callback_dnmsg(self,  **kwargs):
        """Print log info when a new downlink frame message is sent."""
        lgtw_id = kwargs.get("lgtw_id", "")
        tx_time = kwargs.get("tx_time", "")
        dnmsg = kwargs.get("msg", "")

        self.log.info(
            "%s: lGTW %s, new frame sent for transmission. (%d)",
            self.label, lgtw_id, tx_time)
        # TODO CHECK
        if dnmsg:
            self.log.info(
                "%s: xtime=%d, rctx=%d", self.label,
                dnmsg["xtime"], dnmsg["rctx"])
            self.log.info(
                "%s: \n%s", self.label,
                json.dumps(dnmsg, indent=2, sort_keys=True))

    def callback_dnsched(self,  **kwargs):
        """Print log info when a new DN scheduled frame message is sent."""
        lgtw_id = kwargs.get("lgtw_id", "")
        # tx_time = kwargs.get("tx_time", "")
        dnsched = kwargs.get("msg", "")

        self.log.info(
            "%s: lGTW %s, new frames scheduled for transmission.",
            self.label, lgtw_id)
        for frame in dnsched:
            if "rctx" in dnsched:
                self.log.info(
                    "%s: DR=%d, Freq=%d, priority=%d, gpstime=%d, rctx=%d",
                    self.label, frame["DR"], frame["Freq"], frame["priority"],
                    frame["gpstime"], frame["rctx"])
            else:
                self.log.info(
                    "%s: DR=%d, Freq=%d, priority=%d, gpstime=%d",
                    self.label, frame["DR"], frame["Freq"], frame["priority"],
                    frame["gpstime"])
            self.log.info("%s: pdu=%s", self.label, dnsched["pdu"])

    def callback_dn_timesync(self,  **kwargs):
        """Print log info when a new timesync message is sent."""
        lgtw_id = kwargs.get("lgtw_id", "")
        # tx_time = kwargs.get("tx_time", "")
        timesync = kwargs.get("msg", "")

        self.log.info(
            "%s: lGTW %s, timesync message (txtime=%d) sent to lGTW, " +
            "gpstime=%d microsecs since GPS epoch ",
            self.label, lgtw_id, timesync["txtime"], timesync["gpstime"])

    def callback_rmcmd(self,  **kwargs):
        """Print log info when a new remote command message is sent."""
        lgtw_id = kwargs.get("lgtw_id", "")
        # tx_time = kwargs.get("tx_time", "")
        rmcmd = kwargs.get("msg", "")
        args = ""
        for arg in rmcmd["arguments"]:
            args += arg + " "
        self.log.info(
            "%s: lGTW %s, remote command sent to lGTW > %s %s ",
            self.label, lgtw_id, rmcmd["command"], args)

    def callback_dn_rmtsh(self,  **kwargs):
        """Print log info when a new remote shell message is sent."""
        lgtw_id = kwargs.get("lgtw_id", "")
        # tx_time = kwargs.get("tx_time", "")
        rmtsh = kwargs.get("msg", "")
        user = rmtsh.get("user", "")
        term = rmtsh.get("term", "")

        if "start" in rmtsh:
            self.log.info(
                "%s: lGTW %s, remote shell session start, user %s," +
                " term %s ", self.label, lgtw_id, user, term)
        elif "stop" in rmtsh:
            self.log.info(
                "%s: lGTW %s, remote shell session stop, user %s," +
                " term %s ", self.label, lgtw_id, user, term)
        else:
            self.log.info(
                "%s: lGTW %s, current remote shell session state" +
                " query sent, user %s, term %s ", self.label,
                lgtw_id, user, term)

    # Monitoring Round-trip Times
    def callback_rtt_data_rx(self, **kwargs):
        """Print log info when new RTT data is avaliable.

        The field RefTime is calculated from the last received MuxTime adjusted
        by the time interval on the router between the arrival of MuxTime
        and the sending of RefTime.
        Since downlink traffic is less frequent than uplink messages,
        it is likely that a MuxTime is reused to construct multiple RefTime
        fields.
        This means that round-trip measurements are composed of the latency of
        the last downlink message and the most recent uplink message.
        """
        lgtw_id = kwargs.get("lgtw_id", "")
        RefTime = kwargs.get("RefTime", "")
        self.log.info(
            "%s: lGTW %s, new RTT data arrived, RefTime = %f",
            self.label, lgtw_id, RefTime)

    def callback_rtt_query(self, **kwargs):
        """Print log info when new RTT query is sent.

        Note: The field MuxTime contains a float value representing
        a UTC timestamp with fractional seconds and marks the time
        when this message was sent by the LNS.
        """
        lgtw_id = kwargs.get("lgtw_id", "")
        MuxTime = kwargs.get("MuxTime", "")
        self.log.info(
            "%s: lGTW %s, new RTT data sent%s", self.label, lgtw_id,
            ", MuxTime = %f" % 0.0 if isinstance(MuxTime, float) else "")

    def callback_rtt_on(self, **kwargs):
        """Print log info  when RTT query is set to ON."""
        lgtw_id = kwargs.get("lgtw_id", "")
        self.log.info("%s: lGTW %s, RTT set to ON.", self.label, lgtw_id)

    def callback_rtt_off(self, **kwargs):
        """Print log info  when RTT query is set to OFF."""
        lgtw_id = kwargs.get("lgtw_id", "")
        self.log.info("%s: lGTW %s, RTT set to OFF.", self.label, lgtw_id)

    # Gathering Radio Data statistics
    def callback_new_radio_data(self, **kwargs):
        """Print log info when a LoRaWAN Radio GTW radio data is avaliable."""
        lgtw_id = kwargs.get("lgtw_id", "")
        radio_data = kwargs.get("radio_data", "")
        dev_eui = kwargs.get("DevEui", "")
        dev_addr = kwargs.get("DevAddr", "")
        rx_time = kwargs.get("rx_time", 0)

        self.log.info(
            "%s: lGTW %s, New Radio Data. (%d)", self.label,
            lgtw_id, rx_time)
        self.log.info(
            "%s: DevEUI %s, DevAddr %s", self.label,
            dev_eui, dev_addr)
        self.log.info(
            "%s: \n%s", self.label,
            json.dumps(radio_data, indent=2, sort_keys=True))


def launch(context, service_id, label="LoMMTest"):
    """Launch LoMM Test App."""
    return LoMMTest(context=context, service_id=service_id, label=label)
