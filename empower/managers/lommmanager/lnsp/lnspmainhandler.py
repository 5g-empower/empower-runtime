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
"""LNS Basic Station Web Socket Protocol Handler.

Handles the WS connection with a Basic Station lGTW
"""

from datetime import datetime

import struct
import json
import logging
import tornado.websocket

import empower.managers.lommmanager.lnsp as lnsp

from empower.managers.lommmanager.lnsp.lorawangtw import LGtwState
from empower.core.eui64 import EUI64

LOG = logging.getLogger("LoRafNSPMainHandler")


class LNSPMainHandler(tornado.websocket.WebSocketHandler):
    """LNS Basic Station Web Socket Protocol Handler."""

    HANDLERS = [r"/router-(.*)"]
    LABEL = "LoRaWAN Forwarding Network Server"

    lgtw_euid = None
    lgtw = None
    lgtw_ipaddr = None
    rtt_on = False
    last_rtt_time = None
    server = None

    @classmethod
    def urls(cls, **kwargs):
        """Return a list of handlers."""
        return [
            # (r'/router-info/', cls, kwargs),   # Route/Handler/kwargs
            (h, cls, kwargs) for h in cls.HANDLERS  # Route/Handler/kwargs
        ]

    def check_origin(self, origin):
        """Reject all requests with an origin on non specified hosts.

        Use this method a security protection against cross site scripting
        attacks on browsers, since WebSockets are allowed to bypass the
        usual same-origin policies and don’t use CORS headers.

        This is an important security measure: don’t disable it without
        understanding the security implications.

        In particular, if your authentication is cookie-based, you must
        either restrict the origins allowed by check_origin() or implement
        your own XSRF-like protection for websocket connections.
        See these articles for more:
        https://devcenter.heroku.com/articles/websocket-security
        http://www.tornadoweb.org/en/stable/websocket.html#configuration
        """
        return True
        # NOTE Alternative code for check_origin:
        #    allowed = ["https://site1.tld", "https://site2.tld"]
        #    if origin in allowed:
        #        return True

    def initialize(self, server):
        """Initialize LNS protocol WS server."""
        self.server = server

    def to_dict(self):
        """Return dict representation of object."""
        return {"handler": self.HANDLERS,
                "desc": self.LABEL,
                "lgtw_euid": self.lgtw.lgtw_euid.id6,
                "lgtw_ipaddr": self.lgtw.ipaddr}

    # def open(self, lgtw_euid):
    def open(self, *args: str, **kwargs: str):
        """Exec code when a new WebSocket is opened.

        The arguments to `open` are extracted from
        the `tornado.web.URLSpec` regular expression,
        just like the arguments to `tornado.web.RequestHandler.get`.
        """
        lgtw_euid = EUI64(args[0])
        try:
            self.lgtw = self.server.lgtws[lgtw_euid]
        except KeyError:
            LOG.info("Unregistered lGtw (%s), closing connection",
                     lgtw_euid)
            self.close()
            return

        # save lGTW IP address
        self.lgtw.ipaddr = self.request.remote_ip
        self.lgtw.last_seen_ts = datetime.now().timestamp()
        self.lgtw.save()  # REVIEW test
        # save lGTW connection
        self.lgtw.connection = self
        # set lGTW state to CONNECTED
        self.lgtw.set_connected()
        LOG.info("Connected to lGtw %s", self.lgtw.lgtw_euid.id6)

    def on_close(self):
        """Exec code when a existing WebSocket is closed."""
        if self.lgtw and self.lgtw.lgtw_euid:
            LOG.info("LoRa GTW disconnected: %s", self.lgtw.lgtw_euid.id6)
            # reset state
            self.lgtw.set_disconnected()
            self.lgtw.last_seen = datetime.fromtimestamp(
                self.lgtw.last_seen_ts).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            self.lgtw.save()  # REVIEW test
            self.lgtw.connection = None
            self.lgtw = None
        else:
            LOG.info("LoRa GTW disconnected: not a valid GTW")

    def on_message(self, message):
        """Exec code when a new message arrives."""
        rxtime = datetime.now().timestamp()
        if self.lgtw:
            self.lgtw.last_seen_ts = rxtime
            try:
                msg = json.loads(message)
                msgtype = msg['msgtype']
            except ValueError:
                LOG.error("Invalid input: %s", message)
            except KeyError:
                LOG.error("Invalid input: %s", message)
            else:
                # Check message type
                if msgtype not in lnsp.UP_PACKET_TYPES:
                    LOG.error("Unknown message type %s", msgtype)
                    return
                LOG.info("Got a %s message from LGTW %s", msgtype,
                         self.lgtw.lgtw_euid.id6)
                # If lGTW is not online, check if version or new state msg
                if (msgtype not in [lnsp.PT_LGTW_VERSION] and
                        not self.lgtw.is_online()):
                    LOG.info("Got %s message from non connected LGTW %s, \
                             dropping message",
                             msgtype, self.lgtw.lgtw_euid.id6)
                    return
                # Retrieve the msg handler
                msg_handler_name = "_handle_%s" % msgtype
                if hasattr(self, msg_handler_name):
                    msg_handler = getattr(self, msg_handler_name)
                    msg_handler(msg, rxtime)

                # Check if message contains RTT data
                if "RefTime" in msg:
                    self._handle_rtt_data_rx(msg["RefTime"], rxtime)
        else:
            self.close()

    def call_registered_callbacks(self, pt_type, **kwargs):
        """Call registered callbacks."""
        kwargs['lgtw_id'] = self.lgtw.lgtw_euid
        if pt_type in lnsp.EVENT_HANDLERS:
            for handler in lnsp.EVENT_HANDLERS[pt_type]:
                handler(**kwargs)

    def _handle_rtt_data_rx(self, reftime, rxtime):
        """Handle rtt between lgtw and Ctrl data incoming message.

        Args:
            message
        Returns:
            None
        """
        if self.rtt_on:
            # Call registered callbacks
            self.call_registered_callbacks(lnsp.RTT_RX, RefTime=reftime,
                                           MuxTime=self.last_rtt_time,
                                           rxtime=rxtime)

    # Handling uplink messages from lGTW
    def _handle_version(self, lgtw_version, rxtime):
        """Handle an incoming lnsp.PT_LGTW_VERSION message.

        Args:
            version, a VERSION message

        Returns:
            None
        """
        # New connection
        self.lgtw.last_seen_ts = datetime.now().timestamp()
        if self.lgtw.state != LGtwState.ONLINE:
            try:
                self.lgtw.lgtw_version["station"] = lgtw_version["station"]
                self.lgtw.lgtw_version["firmware"] = lgtw_version["firmware"]
                self.lgtw.lgtw_version["package"] = lgtw_version["package"]
                self.lgtw.lgtw_version["model"] = lgtw_version["model"]
                self.lgtw.lgtw_version["protocol"] = lgtw_version["protocol"]
            except KeyError as err:
                LOG.info("Malformmed version message from LoRaWAN GTW (%s)",
                         self.lgtw.lgtw_euid.id6)
                LOG.info(err)
                LOG.info("Closing connection...")
                self.close()
            except Exception:
                LOG.info("Couldn't register lGTW, closing connection...")
                self.close()
                raise
            else:
                if "features" in lgtw_version:
                    # The "features" string is space-separated list of some
                    # of the following keywords:
                    self.lgtw.rmtsh = \
                        lgtw_version["features"].find("rmtsh") > 0
                    # rmtsh: Basic Station supports remote-shell access through
                    # the websocket link established with the LNS.
                    self.lgtw.prod = lgtw_version["features"].find("prod") > 0
                    # prod: Basic Station has been built at production level,
                    # that is, certain test/debug features MAY be disabled.
                    self.lgtw.gps = lgtw_version["features"].find("gps") > 0
                    # gps Basic Station has access to a GPS device.
                else:
                    self.lgtw.rmtsh = False
                    self.lgtw.prod = False
                    self.lgtw.gps = False
                if self.lgtw.prod:
                    # The Basic Station has been built at production level
                    # TODO disable test/debug features
                    pass
                self.send_lgtw_config()
                self.lgtw.set_online()
                # Call registered callbacks
                self.call_registered_callbacks(lnsp.PT_LGTW_VERSION,
                                               lgtw_version=lgtw_version,
                                               rxtime=rxtime)
            self.lgtw.save()

    def _handle_dntxed(self, dntxed_msg, rxtime):
        """Handle an incoming Transmit Confirmation Frame from a device.

        This message is only sent when a frame has been put on air.
        There is no feedback to the LNS if a frame could not be sent
        (e.g., because it was too late, there was a conflict with ongoing
        transmit, or the gateway’s duty cycle was exhausted).

        Args:
            dntxed_msg, a Transmit Confirmation message
        Returns:
            None
        """
        data = {}
        data["rxtime"] = rxtime
        data['dntxed'] = {}
        try:
            data['dntxed']["diid"] = dntxed_msg["diid"]
            # copy of the field diid of the dnmsg message.
            data['dntxed']["DevEui"] = dntxed_msg["DevEui"]
            data['dntxed']["rctx"] = dntxed_msg["rctx"]
            # specifies the antenna used for transmit
            data['dntxed']["xtime"] = dntxed_msg["xtime"]
            # exact internal time when the frame was put on air.
            data['dntxed']["txtime"] = dntxed_msg["txtime"]
            data['dntxed']["gpstime"] = dntxed_msg["gpstime"]
        except KeyError as err:
            LOG.info("Malformed DN TX confirmation message")
            LOG.info(err)
        else:
            # Call registered callbacks
            self.call_registered_callbacks(lnsp.PT_DN_FRAM_TXED, **data)

    def _handle_timesync(self, timesync_msg, rxtime):
        """Handle an incoming Transmit Confirmation Frame from a device.

        **If** Station has access to a PPS signal aligned to GPS seconds,
        it will infer the sychronization to GPS time
        by running a protocol with the LNS.
        To infer the correct GPS time label for a given PPS pulse,
        Station keeps sending timesync upstream messages to the LNS which
        should be promptly answered with a downtream timesync message.

        Args:
            timesync_msg, a Timesync message
        Returns:
            None
        """
        data = {}
        data["rxtime"] = rxtime
        if "gpstime" in timesync_msg:
            # Transferring GPS Time
            try:
                data["xtime"] = timesync_msg["xtime"]
                data["gpstime"] = timesync_msg["gpstime"]
            except KeyError as err:
                LOG.info("Malformed Timesync Message")
                LOG.info(err)
        else:
            try:
                data["txtime"] = timesync_msg["txtime"]
            except KeyError as err:
                LOG.info("Malformed Timesync Message")
                LOG.info(err)
        # Call registered callbacks
        self.call_registered_callbacks(lnsp.PT_DN_TIMESYNC, **data)

    def _handle_rmtsh(self, rmtsh_msg, rxtime):
        """Handle Station response after a remote shell request.

        Station responds with a message describing the current state
        of all sessions.

        Args:
            dntxed_msg, a Transmit Confirmation message

        Returns:
            None
        """
        if not self.lgtw.rmtsh:
            pass

        rmtsh_status = rmtsh_msg.get("rmtsh")
        # TODO implement handling of the Basic Station rmtsh response message
        # Basic Station respond to a rmtsh query from the LNS with
        # a message describing the current state of all sessions:
        # reply_msg = {
        #               "msgtype": "rmtsh",
        #               "rmtsh": [
        #                 {
        #                   "user": STRING,
        #                   "started": BOOL,
        #                   "age": INT,
        #                   "pid": INT
        #                 },
        #                 ..
        #               ]
        #             }
        # Where:
        # age: is the time in seconds since the input/output action
        #      on this remote shell session.
        # pid: is the local process identifier of the started shell.
        # started: indicates that the shell process is actually running.
        # user: describes the user who is operating the session.
        #       For Station this is just informational context.

        # Call registered callbacks
        self.call_registered_callbacks(lnsp.PT_RMT_SH,
                                       rmtsh_status=rmtsh_status,
                                       rxtime=rxtime)

    # Handling uplink messages from lEndDev
    def _handle_radio_data(self, rx_msg, rxtime):
        """Handle an radio metatadata of incoming message.

        Args:
            message
        Returns:
            None
        """
        data = {}
        data['radio_data'] = {}
        data['radio_data']['DR'] = rx_msg['DR']
        # data rate received [1..15]
        data['radio_data']['Freq'] = rx_msg['Freq']
        # receive frequency in Hz
        data['radio_data']["rssi"] = float(rx_msg['upinfo']["rssi"])
        data['radio_data']["snr"] = float(rx_msg['upinfo']["snr"])
        data['radio_data']["radio_unit"] = \
            (rx_msg['upinfo']["rctx"] >> 56) & 0x7F
        # specifies the antenna used
        # NOTE Encoding of rctx:
        #   6-0   radio unit
        # specifies the antenna used for transmit/rx
        data['radio_data']["rctx"] = rx_msg['upinfo']["rctx"]
        data['radio_data']["rxtime"] = rx_msg['upinfo']["rxtime"]
        data['radio_data']["xtime"] = rx_msg['upinfo']["xtime"]
        # internal time of the lGTW
        # NOTE Encoding of xtime:
        #  bits:
        #   63    sign (always positive)
        #   62-56 radio unit where the time stamp originated from (max 128)
        #   55-48 random value to disambiguate different SX1301 sessions
        #         (never 0, aka valid xtime is never 0)
        #   47-0  microseconds since SX1301 start
        #         (rollover every 9y >> uptime of sessions)
        #
        # data["xtime"] = rx_msg['upinfo']["xtime"]
        # data["xtime"] = rx_msg['upinfo']["xtime"] & 0xFFFFFFFF
        #                 #TOCHECK 32bit
        #
        # xtime2txunit(xtime) (xtime >> 56) & 0x7F
        # xtime2sess(xtime)   (xtime >> 48) & 0xFF
        # xtime2rctx(xtime)   (xtime & 0xFFFFFFFFFFFF)
        data["gpstime"] = rx_msg['upinfo']["gpstime"]
        # gpstime is the receive timetamp of the frame expressed
        # in microseconds since GPS epoch.
        # NOTE if Station does not have access to a PPS signal synchronized
        # to GPS time, the value of this field is 0.
        data["rx_time"] = rxtime
        data["DevAddr"] = rx_msg.get("DevAddr")
        data["DevEui"] = rx_msg.get("DevEui")

        # Call registered callbacks
        self.call_registered_callbacks(lnsp.RCV_RADIO_DATA, **data)

        return data['radio_data']

    def _handle_jreq(self, join_msg, rxtime):
        """Handle an incoming Join Request from a device.

        Args:
            join_msg, a JOIN message
        Returns:
            None
        """
        data = {}
        data["radio_data"] = self._handle_radio_data(join_msg, rxtime)
        data["rxtime"] = rxtime
        data["join_data"] = {}
        try:
            data["join_data"]["MHdr"] = join_msg["MHdr"]
            data["join_data"]["JoinEui"] = EUI64(join_msg["JoinEui"])
            data["join_data"]["DevEui"] = EUI64(join_msg["DevEui"])
            data["join_data"]["DevNonce"] = join_msg["DevNonce"]
            data["join_data"]["MIC"] = join_msg["MIC"] & (2**32 - 1)
            data["xtime"] = join_msg['upinfo']["xtime"]
            # internal time of the lGTW
            data["rctx"] = join_msg['upinfo']["rctx"]
            # specifies the antenna used
        except KeyError as err:
            LOG.info("Malformed Join Request")
            LOG.info(err)
        else:
            data["PhyPayload"] = struct.pack("<BQQHI", join_msg["MHdr"],
                                             int(data["join_data"]["JoinEui"]),
                                             int(data["join_data"]["DevEui"]),
                                             # TODO check if int(value,16)
                                             # is needed
                                             #  int(data["join_data"]["JoinEui"],
                                             #      16),
                                             #  int(data["join_data"]["DevEui"],
                                             #      16),
                                             join_msg["DevNonce"] & 0xFFFF,
                                             join_msg["MIC"] &
                                             (2**32 - 1)).hex()
            if data["join_data"]["DevEui"] in self.server.lenddevs:
                LOG.info(data["join_data"])
                # TODO implementation of Join Data handling
            else:
                LOG.info("Device %s  is not in the database",
                         data["join_data"]["DevEui"])

            # Call registered callbacks
            data["msg"] = join_msg
            self.call_registered_callbacks(lnsp.PT_JOIN_REQ, **data)

    def _handle_updf(self, updf_msg, rxtime):
        """Handle an incoming Data Frame from a device.

        Args:
            upmsg, a Uplink message
        Returns:
            None
        """
        data = {}
        data["radio_data"] = self._handle_radio_data(updf_msg, rxtime)
        data["rxtime"] = rxtime
        data["updf_data"] = {}
        try:
            data["updf_data"]["MHdr"] = updf_msg["MHdr"]
            data["updf_data"]["DevAddr"] = updf_msg["DevAddr"] & (2**32 - 1)
            data["updf_data"]["FCtrl"] = updf_msg["FCtrl"]
            data["updf_data"]["FCnt"] = updf_msg["FCnt"]
            data["updf_data"]["FOpts"] = updf_msg["FOpts"]
            data["updf_data"]["FPort"] = updf_msg["FPort"]
            data["updf_data"]["FRMPayload"] = updf_msg["FRMPayload"]
            data["updf_data"]["MIC"] = updf_msg["MIC"] & (2**32 - 1)
            data["xtime"] = updf_msg['upinfo']["xtime"]
            # internal time of the lGTW
            data["rctx"] = updf_msg['upinfo']["rctx"]
            # specifies the antenna used
        except KeyError as err:
            LOG.info("Malformed Uplink Frame")
            LOG.info(err)
            LOG.info(updf_msg)
        else:
            # Call registered callbacks
            fopts = bytes.fromhex(updf_msg['FOpts']
                                  if updf_msg['FOpts'] else '')
            fport = bytes.fromhex('%02x' % updf_msg['FPort']
                                  if updf_msg['FPort'] >= 0 else '')
            frmpayload = bytes.fromhex(updf_msg['FRMPayload']
                                       if updf_msg['FRMPayload'] else '')
            data["PhyPayload"] = struct.pack(
                "<BIBBB{}s{}s{}sI".format(len(fopts),
                                          len(fport),
                                          len(frmpayload)),
                updf_msg['MHdr'],
                updf_msg['DevAddr'],
                updf_msg['FCtrl'] & 0xFF,
                updf_msg['FCnt'] & 0xFF,
                (updf_msg['FCnt'] >> 8) & 0xFF,
                fopts,
                fport,
                frmpayload,
                (updf_msg['MIC'] & (2**32 - 1))).hex()

            data["msg"] = updf_msg
            self.call_registered_callbacks(lnsp.PT_UP_DATA_FRAME, **data)

    def _handle_propdf(self, updf_msg, rxtime):
        """Handle an incoming Proprietary Data Frame from a device.

        Args:
            upmsg, a Proprietary Uplink message
        Returns:
            None
        """
        data = {}
        data["radio_data"] = self._handle_radio_data(updf_msg, rxtime)
        data["rxtime"] = rxtime
        try:
            data["FRMPayload"] = updf_msg["FRMPayload"]
            data["xtime"] = updf_msg['upinfo']["xtime"]
            # internal time of the lGTW
            data["rctx"] = updf_msg['upinfo']["rctx"]
            # specifies the antenna used
        except KeyError as err:
            LOG.info("Malformed Proprietary Frame")
            LOG.info(err)
        else:
            # Call registered callbacks
            data["msg"] = updf_msg
            self.call_registered_callbacks(lnsp.PT_UP_PROP_FRAME, **data)

    # Handling Downlink Messages
    def send_message(self, msgtype, msg):
        """Download Frame."""
        if msgtype in lnsp.DN_PACKET_TYPES:
            msg['msgtype'] = msgtype
            if self.lgtw.is_send_rtt_on():
                msg['MuxTime'] = datetime.now().timestamp()
                # float value representing a UTC timestamp with fractional
                # seconds and marks the time when this
                # message is sent by the LNS

            self.write_message(json.dumps(msg))
            tx_time = datetime.now().timestamp()
            LOG.info("Message %s sent", msg['msgtype'])

            if self.lgtw.is_send_rtt_on():
                self.last_rtt_time = msg['MuxTime']
                # call RTT callbacks
                self.call_registered_callbacks(lnsp.RTT_TX,
                                               muxtime=self.last_rtt_time)
            # call msg sent callbacks
            self.call_registered_callbacks(msgtype, msg=msg, tx_time=tx_time)

    # Handling send downlink message to lEndDev
    def send_lgtw_downlink_frame(self, dev_eui, pdu, params):
        """Send Downlink Frame to lGTW."""
        # TODO implement handling of dn_frame format (Class A/B/C device)
        # TODO implement handling of MAC Commands, Port etc. at LNS level
        # NOTE handling only class A devices
        #  Class A
        #  A Class A downlink frame is a response to a previously sent uplink.
        #  The layout for Class A REQUIRES the following fields:
        try:
            msg = {
                "DevEui": dev_eui,
                "dC": 0,                  # class A
                "diid": params["diid"],
                # INT64, a number issued by the LNS to identify
                # a particular device interaction.
                "pdu": pdu,
                # "HEX", radio frame as it will be put on air.
                "RxDelay": params["RxDelay"],  # INT(0..15),  # tx parameters
                "RX1DR": params["RX1DR"],    # INT(0..15),  # tx parameters
                "RX1Freq": params["RX1Freq"],  # INT,  # tx parameters
                "RX2DR": params["RX2DR"],    # INT(0..15),  # tx parameters
                "RX2Freq": params["RX2Freq"],  # INT,  # tx parameters
                "priority": params["priority"],  # INT(0..255)
                # tx parameters
                "xtime": params["xtime"],    # INT64
                # values that originate from the corresponding uplink message
                "rctx": params["rctx"],     # INT64
                # values that originate from the corresponding uplink message
                }
        finally:
            # TODO Class B & C (send_lgtw_downlink_frame)
            # TODO Check how to select tx parameters (send_lgtw_downlink_frame)
            self.send_message(lnsp.PT_DN_MSG, msg)

    def send_lgtw_dnschede(self, schedule):
        """Send Multicast Schedule to lGTW.

        Messages of type dnsched can be use to schedule a set of multicast
        messages in one go. Each of the message elements needs to specify
        a GPS time at which it shall be sent.
        This type of transmission does not generate dntxed responses
        from Station.

        {
          "msgtype": "dnsched",
          "schedule": [
            {
              "pdu": "HEX",
              "DR": INT(0..15),
              "Freq": INT,
              "priority": INT(0..255),
              "gpstime": INT64,
              "rctx": INT64
            },
            ...
          ]
        }

        The field rctx is OPTIONAL but MAY be used to select
        an antenna preference.
        LNS MAY copy this field from a previous Class A uplink and
        guide Station to use the same antenna which received
        that Class A uplink.
        """
        # TODO implement handling of multicast schedule format
        msg = {}
        msg['schedule'] = schedule
        self.send_message(lnsp.PT_DN_SCHED, msg)

    # Handling send downlink messages to lGTW
    def send_lgtw_config(self):
        """Send lGTW configuration."""
        # call registered callbacks
        self.call_registered_callbacks(lnsp.PT_DN_MSG,
                                       config=self.lgtw.lgtw_config)
        msg = self.lgtw.lgtw_config.copy()
        self.send_message(lnsp.PT_CONFIG, msg)

    def send_lgtw_timesync_gps_time(self, xtime, gpstime):
        """Send GPS Time to GTW.

        The LNS SHALL periodically send the following message to
        lGTW to transfer GPS time
        """
        # call registered callbacks
        self.call_registered_callbacks(lnsp.PT_DN_TIMESYNC,
                                       xtime=xtime,
                                       gpstime=gpstime)
        msg = {
            "xtime": xtime,
            "gpstime": gpstime
        }
        # TODO implement handling of GPS timesync
        self.send_message(lnsp.PT_TIMESYNC, msg)

    def send_lgtw_timesync_replay(self, txtime, gpstime):
        """Send GPS Time to lGTW as a timesync replay.

        the downstream response SHOULD be sent by the LNS immediately
        after reception of the corresponding upstream timesync message.
        """
        msg = {
            "txtime": int(txtime),
            "gpstime": int(gpstime)
        }
        # TODO implement timesync
        self.send_message(lnsp.PT_TIMESYNC, msg)

    # Handling remote shell and remote commands """
    def send_lgtw_rmcmd(self, command, arguments):
        """Execute a remote command on lGTW."""
        params = {
            "command": command,
            "arguments": arguments
        }
        # TODO implement rmtsh
        self.send_message(lnsp.PT_RUN_CMD, params)

    def send_lgtw_rmtsh_start(self, user, term):
        """Open a remote shell with the LGTW."""
        if self.lgtw.rmtsh:
            params = {
                "user": user,
                "term": term,
                "start": 1
            }
            # TODO implement rmtsh
            self.send_message(lnsp.PT_RMT_SH, params)
            # set status to rmtsh
            if not self.lgtw.is_rmt_shell():
                self.lgtw.set_rmt_shell()
        else:
            # NOTE rmtsh unsupported
            pass

    def send_lgtw_rmtsh_stop(self, user, term):
        """Stop a remote shell with the LGTW."""
        if self.lgtw.rmtsh:
            if self.lgtw.is_rmt_shell():
                params = {
                    "user": user,
                    "term": term,
                    "stop": 1
                }
                # TODO implement rmtsh
                self.send_message(lnsp.PT_RMT_SH, params)
                # set status to ONLINE
                self.lgtw.set_online()
        else:
            # TODO RMTSH unsupported (send_lgtw_rmtsh_stop)
            pass

    def send_lgtw_rmtsh_query(self, user, term):
        """Query current remote shell session state."""
        if self.lgtw.rmtsh:
            if self.lgtw.is_rmt_shell():
                params = {
                    "user": user,
                    "term": term
                }
                self.send_message(lnsp.PT_RMT_SH, params)
            else:
                # TODO implement rmtsh error message
                pass
        else:
            # NOTE RMTSH unsupported
            pass

    def send_lgtw_send_remote_shell_record(self, binary_record):
        """Send shell session binary record."""
        if self.lgtw.is_rmt_shell():
            self.write_message(binary_record)
        else:
            # TODO implement rmtsh error message
            pass

    # Handling lGTW Events
    def lgtw_new_state(self, old_state, new_state):
        """Notify a lGtw new state."""
        # Call registered callbacks
        self.call_registered_callbacks(lnsp.NEW_STATE,
                                       old_state=old_state.value,
                                       new_state=new_state.value)

    # Handling RTT Events
    def rtt_on_set(self):
        """Call callbacks when RTT is on."""
        self.call_registered_callbacks(lnsp.NEW_RTT_ON)

    def rtt_off_set(self):
        """Call callbacks when RTT is off."""
        self.call_registered_callbacks(lnsp.NEW_RTT_OFF)
