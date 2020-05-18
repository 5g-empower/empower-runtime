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
"""LNS Protocol Manager."""

LORAWAN_VERSION = "1.0"

# DEFAULTS
DEFAULT_OWNER = 0
DEFAULT_TENANT = "::0"

# MSG TYPES

# uplink msgtypes lgtw to lns
PT_LGTW_VERSION = "version"  # TOCHECK should be "version"
PT_JOIN_REQ = "jreq"
PT_UP_DATA_FRAME = "updf"
PT_UP_PROP_FRAME = "propdf"
PT_DN_FRAM_TXED = "dntxed"
PT_TIMESYNC = "timesync"
PT_RMT_SH = "rmtsh"


# downlink msgtypes lns to lgtw
PT_CONFIG = "router_config"
PT_DN_MSG = "dnmsg"
PT_DN_SCHED = "dnsched"
PT_RUN_CMD = "rmcmd"
PT_DN_TIMESYNC = "dn_timesync"
PT_DN_RMT_SH = "dn_rmtsh"

UP_PACKET_TYPES = [
    PT_LGTW_VERSION,
    PT_JOIN_REQ,
    PT_UP_DATA_FRAME,
    PT_UP_PROP_FRAME,
    PT_DN_FRAM_TXED,
    PT_TIMESYNC,
    PT_RMT_SH
    ]

DN_PACKET_TYPES = [
    PT_CONFIG,
    PT_DN_MSG,
    PT_DN_SCHED,
    PT_RUN_CMD,
    PT_TIMESYNC,
    PT_RMT_SH
    ]

# Additional processing on updf
RCV_RADIO_DATA = "new_radio_data"

# RTT between LNS and lGTW calc
NEW_RTT_ON = "rtt_on"      # RTT calc activated
NEW_RTT_OFF = "rtt_off"     # RTT calc deactivated
RTT_TX = "rtt_query"   # the LNS sends a MuxTime to the lGTW
RTT_RX = "rtt_data_rx"  # the LNS recieves a RefTime from lGTW as reply

# LNS state
NEW_STATE = "new_state_transition"

# EVENTS
# maps types mapping with handlers
EVENT_HANDLERS = {}
# lgtw to lns
EVENT_HANDLERS[PT_LGTW_VERSION] = []
EVENT_HANDLERS[PT_JOIN_REQ] = []
EVENT_HANDLERS[PT_UP_DATA_FRAME] = []
EVENT_HANDLERS[PT_UP_PROP_FRAME] = []
EVENT_HANDLERS[PT_DN_FRAM_TXED] = []
EVENT_HANDLERS[PT_TIMESYNC] = []
EVENT_HANDLERS[PT_RMT_SH] = []
# lns to lgtw
EVENT_HANDLERS[PT_CONFIG] = []
EVENT_HANDLERS[PT_DN_MSG] = []
EVENT_HANDLERS[PT_DN_SCHED] = []
EVENT_HANDLERS[PT_RUN_CMD] = []
EVENT_HANDLERS[PT_DN_TIMESYNC] = []
EVENT_HANDLERS[PT_DN_RMT_SH] = []

EVENT_HANDLERS[RCV_RADIO_DATA] = []

EVENT_HANDLERS[RTT_TX] = []
EVENT_HANDLERS[RTT_RX] = []

EVENT_HANDLERS[NEW_STATE] = []
EVENT_HANDLERS[NEW_RTT_ON] = []
EVENT_HANDLERS[NEW_RTT_OFF] = []


def register_message(pt_type):
    """Register new message and a new handler."""
    if pt_type not in EVENT_HANDLERS:
        EVENT_HANDLERS[pt_type] = []


def register_callbacks(app, callback_str='callback_'):
    """Register callbacks."""
    for event in EVENT_HANDLERS:
        handler_name = callback_str + event
        if hasattr(app, handler_name):
            handler = getattr(app, handler_name)
            EVENT_HANDLERS[event].append(handler)


def unregister_callbacks(app, callback_str='callback_'):
    """Unregister callbacks."""
    for event in EVENT_HANDLERS:
        handler_name = callback_str + event
        if hasattr(app, handler_name):
            handler = getattr(app, handler_name)
            EVENT_HANDLERS[event].remove(handler)


def register_callback(event, handler):
    """Register new message and a new handler."""
    if event not in EVENT_HANDLERS:
        raise KeyError("EVENT_HANDLER %s undefined" % event)
    EVENT_HANDLERS[event].append(handler)


def unregister_callback(event, handler):
    """Register new message and a new handler."""
    if event not in EVENT_HANDLERS:
        raise KeyError("EVENT_HANDLER %s undefined" % event)
    EVENT_HANDLERS[event].remove(handler)


def lenddevs_by_dev_addr(lenddevs):
    """Return lGTWs in this project."""
    output = {}
    for dev_eui, lenddev in lenddevs.items():
        dev_addr = lenddev.dev_addr
        if dev_addr:
            if isinstance(dev_addr, int):
                output[dev_addr] = dev_eui
            else:
                output[int(dev_addr, 16)] = dev_eui
    return output
