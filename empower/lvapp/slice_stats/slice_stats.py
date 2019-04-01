#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

"""Slice statistics module."""

from construct import UBInt8
from construct import UBInt32
from construct import Bytes
from construct import Container
from construct import Struct

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.dscp import DSCP
from empower.datatypes.ssid import WIFI_NWID_MAXSIZE
from empower.lvapp.lvappserver import ModuleLVAPPWorker
from empower.core.module import ModulePeriodic
from empower.core.resourcepool import ResourceBlock
from empower.lvapp import PT_VERSION

from empower.main import RUNTIME


PT_SLICE_STATS_REQUEST = 0x59
PT_SLICE_STATS_RESPONSE = 0x60

SLICE_STATS_REQUEST = \
    Struct("slice_stats_request", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("hwaddr", 6),
           UBInt8("channel"),
           UBInt8("band"),
           UBInt8("dscp"),
           Bytes("ssid", WIFI_NWID_MAXSIZE + 1))

SLICE_STATS_RESPONSE = \
    Struct("slice_stats_response", UBInt8("version"),
           UBInt8("type"),
           UBInt32("length"),
           UBInt32("seq"),
           UBInt32("module_id"),
           Bytes("wtp", 6),
           UBInt32("deficit_used"),
           UBInt32("max_queue_length"),
           UBInt32("tx_packets"),
           UBInt32("tx_bytes"))


class SliceStats(ModulePeriodic):
    """SliceStats object.

    This primitive tracks the statisitcs of a certain slice.

    For example (from within an app):
        self.slice_stats(block=block,
                         every=2000,
                         callback=self.slices_stats_ callback)

    This will call the method self.slices_stats_ callback every 2 seconds and
    will report some information about the slice, including: tx/rx bytes, the
    deficit used, and the maximum length of the queue.
    """

    MODULE_NAME = "slice_stats"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    def __init__(self):

        super().__init__()

        # parameters
        self._block = None
        self._dscp = DSCP()

        # data structures
        self.slice_stats = {}

    def __eq__(self, other):

        return super().__eq__(other) and self.block == other.block and \
          self.dscp == other.dscp

    @property
    def dscp(self):
        """DSCP code."""

        return self._dscp

    @dscp.setter
    def dscp(self, value):
        self._dscp = DSCP(value)

    @property
    def block(self):
        """Block."""

        return self._block

    @block.setter
    def block(self, value):

        if isinstance(value, ResourceBlock):

            self._block = value

        elif isinstance(value, dict):

            wtp = RUNTIME.wtps[EtherAddress(value['wtp'])]

            if 'hwaddr' not in value:
                raise ValueError("Missing field: hwaddr")

            if 'channel' not in value:
                raise ValueError("Missing field: channel")

            if 'band' not in value:
                raise ValueError("Missing field: band")

            if 'wtp' not in value:
                raise ValueError("Missing field: wtp")

            # Check if block is valid
            incoming = ResourceBlock(wtp, EtherAddress(value['hwaddr']),
                                     int(value['channel']),
                                     int(value['band']))

            match = [block for block in wtp.supports if block == incoming]

            if not match:
                raise ValueError("No block specified")

            if len(match) > 1:
                raise ValueError("More than one block specified")

            self._block = match[0]

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['block'] = self.block.to_dict()
        out['dscp'] = self.dscp
        out['slice_stats'] = self.slice_stats

        return out

    def run_once(self):
        """ Send out request. """

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]
        wtp = self.block.radio

        if wtp.addr not in tenant.wtps:
            self.log.info("WTP %s not found", wtp.addr)
            self.unload()
            return

        if not wtp.connection or wtp.connection.stream.closed():
            self.log.info("WTP %s not connected", wtp.addr)
            self.unload()
            return

        self.log.info("Sending %s request to %s (id=%u)",
                      self.MODULE_NAME, wtp.addr, self.module_id)

        stats_req = Container(version=PT_VERSION,
                              type=PT_SLICE_STATS_REQUEST,
                              length=SLICE_STATS_REQUEST.sizeof(),
                              seq=wtp.seq,
                              module_id=self.module_id,
                              hwaddr=self.block.hwaddr.to_raw(),
                              channel=self.block.channel,
                              band=self.block.band,
                              dscp=self.dscp.to_raw(),
                              ssid=tenant.tenant_name.to_raw())

        msg = SLICE_STATS_REQUEST.build(stats_req)
        wtp.connection.stream.write(msg)

    def handle_response(self, response):
        """Handle an incoming STATS_RESPONSE message.
        Args:
            stats, a STATS_RESPONSE message
        Returns:
            None
        """

        # update this object
        self.slice_stats = {
            'tx_bytes': response.tx_bytes,
            'tx_packets': response.tx_packets,
            'deficit_used': response.deficit_used,
            'max_queue_length': response.max_queue_length
        }

        if self.tenant_id not in self.block.slice_stats:
            self.block.slice_stats[self.tenant_id] = {}

        self.block.slice_stats[self.tenant_id][self.dscp] = \
            self.slice_stats

        # call callback
        self.handle_callback(self)


class SliceStatsWorker(ModuleLVAPPWorker):
    """Counter worker."""

    pass


def slice_stats(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[SliceStatsWorker.__module__]
    return worker.add_module(**kwargs)


def bound_slice_stats(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return slice_stats(**kwargs)


setattr(EmpowerApp, SliceStats.MODULE_NAME, bound_slice_stats)


def launch():
    """ Initialize the module. """

    return SliceStatsWorker(SliceStats, PT_SLICE_STATS_RESPONSE,
                            SLICE_STATS_RESPONSE)
