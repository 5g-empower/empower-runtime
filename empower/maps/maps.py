#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Common channel quality and conflict maps module."""

import tornado.web
import tornado.httpserver
import uuid

from construct import Container
from construct import Struct
from construct import Array
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import SBInt32
from construct import Sequence

from empower.datatypes.etheraddress import EtherAddress
from empower.core.resourcepool import CQM
from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import ResourcePool
from empower.core.module import ModuleHandler
from empower.core.module import ModuleWorker
from empower.core.module import Module
from empower.lvapp import PT_VERSION
from empower.core.module import handle_callback

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


POLLER_ENTRY_TYPE = Sequence("img_entries",
                             Bytes("addr", 6),
                             UBInt32("last_rssi_std"),
                             SBInt32("last_rssi_avg"),
                             UBInt32("last_packets"),
                             UBInt32("hist_packets"),
                             SBInt32("ewma_rssi"),
                             SBInt32("sma_rssi"))

POLLER_REQUEST = Struct("poller_request", UBInt8("version"),
                        UBInt8("type"),
                        UBInt16("length"),
                        UBInt32("seq"),
                        UBInt32("poller_id"),
                        Bytes("addrs", 6),
                        Bytes("hwaddr", 6),
                        UBInt8("channel"),
                        UBInt8("band"))

POLLER_RESP_MSG = Struct("poller_response", UBInt8("version"),
                         UBInt8("type"),
                         UBInt16("length"),
                         UBInt32("seq"),
                         UBInt32("poller_id"),
                         Bytes("wtp", 6),
                         Bytes("hwaddr", 6),
                         UBInt8("channel"),
                         UBInt8("band"),
                         UBInt16("nb_entries"),
                         Array(lambda ctx: ctx.nb_entries, POLLER_ENTRY_TYPE))


class Maps(Module):
    """ A maps poller. """

    REQUIRED = ['module_type', 'worker', 'tenant_id', 'block']

    _addrs = EtherAddress('FF:FF:FF:FF:FF:FF')
    _block = None

    def __eq__(self, other):

        return super().__eq__(other) and \
            self.addrs == other.addrs and \
            self.block == other.block

    @property
    def addrs(self):
        return self._addrs

    @addrs.setter
    def addrs(self, value):
        self._addrs = EtherAddress(value)

    @property
    def block(self):
        return self._block

    @block.setter
    def block(self, value):

        if not isinstance(value, ResourceBlock):
            raise ValueError("Expected ResourceBlock, got %s", type(value))

        wtp = RUNTIME.wtps[value.radio.addr]

        requested = ResourcePool()
        requested.add(value)

        match = wtp.supports & requested

        if len(match) > 1:
            raise ValueError("More than one block specified")

        if not match:
            raise ValueError("No block specified")

        self._block = match.pop()

    @property
    def maps(self):
        """ Return a JSON-serializable dictionary. """

        map_type = self.worker.MODULE_NAME
        if hasattr(self.block, map_type):
            return getattr(self.block, map_type)
        else:
            return {}

    def to_dict(self):
        """ Return a JSON-serializable dictionary. """

        out = super().to_dict()

        out['maps'] = {str(k): v for k, v in self.maps.items()}
        out['addrs'] = self.addrs
        out['block'] = self.block.to_dict()

        del out['block']['ucqm']
        del out['block']['ncqm']

        return out

    def run_once(self):
        """ Send out request. """

        if self.tenant_id not in RUNTIME.tenants:
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.block.radio.addr not in tenant.wtps:
            return

        if not self.block.radio.connection:
            return

        self.send_poller_request(self.block.radio, self.addrs, self.block)

    def send_poller_request(self, wtp, target, block):
        """ Send a poller request message.

        Args:
            module_id: the poller id
            wtp: a WTP object
            target: an EtherAddress object
            block: a ResourceBlock object
        Returns:
            None
        """

        req = Container(version=PT_VERSION,
                        type=self.worker.POLLER_REQ_MSG_TYPE,
                        length=26,
                        seq=wtp.seq,
                        poller_id=self.module_id,
                        wtp=wtp.addr.to_raw(),
                        addrs=target.to_raw(),
                        hwaddr=block.hwaddr.to_raw(),
                        channel=block.channel,
                        band=block.band)

        LOG.info("Sending %s request to %s (id=%u)",
                 self.worker.MODULE_NAME,
                 block,
                 self.module_id)

        msg = POLLER_REQUEST.build(req)
        wtp.connection.stream.write(msg)


class MapsHandler(ModuleHandler):
    """ Module handler. Used to view and manipulate modules. """

    def post(self, *args, **kwargs):
        """ Create a new module.

        Args:
            [0]: tenant_id

        Request:
            version: the protocol version (1.0)

        Example URLs:

            POST /api/v1/tenants/EmPOWER/<module>
        """

        try:

            if len(args) != 1:
                raise ValueError("Invalid URL")

            tenant_id = uuid.UUID(args[0])

            request = tornado.escape.json_decode(self.request.body)

            if "version" not in request:
                raise ValueError("missing version element")

            if "wtp" not in request:
                raise ValueError("missing wtp element")

            if "hwaddr" not in request:
                raise ValueError("missing hwaddr element")

            if "band" not in request:
                raise ValueError("missing band element")

            if "channel" not in request:
                raise ValueError("missing channel element")

            del request['version']
            request['tenant_id'] = tenant_id
            request['module_type'] = self.worker.MODULE_NAME
            request['worker'] = self.worker

            wtp_addr = EtherAddress(request['wtp'])
            wtp = RUNTIME.tenants[tenant_id].wtps[wtp_addr]

            channel = int(request['channel'])
            band = int(request['band'])
            hwaddr = EtherAddress(request['hwaddr'])

            del request['wtp']
            del request['channel']
            del request['band']
            del request['hwaddr']

            request['block'] = ResourceBlock(wtp, hwaddr, channel, band)

            module = self.worker.add_module(**request)

            self.set_header("Location", "/api/v1/tenants/%s/%s/%s" %
                            (module.tenant_id,
                             self.worker.MODULE_NAME,
                             module.module_id))

            self.set_status(201, None)

        except KeyError as ex:
            self.send_error(404, message=ex)
        except ValueError as ex:
            self.send_error(400, message=ex)


class MapsWorker(ModuleWorker):
    """ Poller worker. """

    MODULE_NAME = None
    MODULE_HANDLER = None
    MODULE_TYPE = None

    POLLER_REQ_MSG_TYPE = None
    POLLER_RESP_MSG_TYPE = None

    def handle_poller_response(self, message):
        """Handle an incoming poller response message.
        Args:
            message, a poller response message
        Returns:
            None
        """

        if message.poller_id not in self.modules:
            return

        wtp_addr = EtherAddress(message.wtp)

        if wtp_addr not in RUNTIME.wtps:
            return

        wtp = RUNTIME.wtps[wtp_addr]
        hwaddr = EtherAddress(message.hwaddr)
        incoming = ResourcePool()
        incoming.add(ResourceBlock(wtp, hwaddr, message.channel, message.band))

        matching = (wtp.supports & incoming).pop()

        LOG.info("Received %s response from %s (id=%u)",
                 self.MODULE_NAME,
                 matching,
                 message.poller_id)

        # find poller object
        poller = self.modules[message.poller_id]

        # handle the message
        map_type = self.MODULE_NAME
        setattr(poller.block, map_type, CQM())
        map_entry = getattr(poller.block, map_type)

        for entry in message.img_entries:

            addr = EtherAddress(entry[0])

            if not addr.match(poller.addrs):
                continue

            value = {'addr': addr,
                     'last_rssi_std': entry[1] / 1000.0,
                     'last_rssi_avg': entry[2] / 1000.0,
                     'last_packets': entry[3],
                     'hist_packets': entry[4],
                     'ewma_rssi': entry[5] / 1000.0,
                     'sma_rssi': entry[6] / 1000.0}

            map_entry[addr] = value

        # call callback
        handle_callback(poller, poller)
