#!/usr/bin/env python3
#
# Copyright (c) 2016, Estefanía Coronado
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

"""Multicast management app with handover support."""

import tornado.web
import tornado.httpserver
import time
import datetime
import sys
import statistics

from empower.core.app import EmpowerApp
from empower.core.resourcepool import TX_MCAST
from empower.core.resourcepool import TX_MCAST_DMS
from empower.core.resourcepool import TX_MCAST_LEGACY
from empower.core.resourcepool import TX_MCAST_DMS_H
from empower.core.resourcepool import TX_MCAST_LEGACY_H
from empower.core.tenant import T_TYPE_SHARED
from empower.datatypes.etheraddress import EtherAddress
from empower.main import RUNTIME
from empower.apps.mcast.mcastwtp import MCastWTPInfo
from empower.apps.mcast.mcastclient import MCastClientInfo

import empower.logger
LOG = empower.logger.get_logger()


class McastLegacy(EmpowerApp):


    """Mobility manager app with multicast rate adaptation support.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        (old) ./empower-runtime.py apps.mcast.mcast:52313ecb-9d00-4b7d-b873-b55d3d9ada26
        (new) ./empower-runtime.py apps.mcast.mcastrssi --tenant_id=be3f8868-8445-4586-bc3a-3fe5d2c17339

    """

    def __init__(self, **kwargs):

        EmpowerApp.__init__(self, **kwargs)

        self.__mcast_clients = []
        self.__mcast_wtps = [] 
        self.__mcast_addr = EtherAddress("01:00:5e:00:00:fb")

        # Register an lvap join event
        self.lvapjoin(callback=self.lvap_join_callback)
        self.lvapleave(callback=self.lvap_leave_callback)
        # Register an wtp up event
        self.wtpup(callback=self.wtp_up_callback)
        self.wtpdown(callback=self.wtp_down_callback)


    @property
    def mcast_clients(self):
        """Return current multicast clients."""
        return self.__mcast_clients

    @mcast_clients.setter
    def mcast_clients(self, mcast_clients_info):
        self.__mcast_clients = mcast_clients_info

    @property
    def mcast_wtps(self):
        """Return current multicast wtps."""
        return self.__mcast_wtps

    @mcast_wtps.setter
    def mcast_wtps(self, mcast_wtps_info):
        self.__mcast_wtps = mcast_wtps_info

    @property
    def mcast_addr(self):
        """Return mcast_addr used."""
        return self.__mcast_addr

    @mcast_addr.setter
    def mcast_addr(self, mcast_addr):
        self.__mcast_addr = mcast_addr

    def txp_bin_counter_callback(self, counter):
        """Counters callback."""

        self.log.info("Mcast address %s packets %u bytes %u", counter.mcast,
                      counter.tx_packets[0], counter.tx_bytes[0])

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == counter.block.hwaddr:
                if counter.mcast in entry.last_txp_bin_tx_pkts_counter:
                    entry.last_tx_pkts[counter.mcast] = counter.tx_packets[0] - entry.last_txp_bin_tx_pkts_counter[counter.mcast]
                else:
                    entry.last_tx_pkts[counter.mcast] = counter.tx_packets[0]
                entry.last_txp_bin_tx_pkts_counter[counter.mcast] = counter.tx_packets[0]
                if counter.mcast in entry.last_txp_bin_tx_bytes_counter:
                    entry.last_tx_bytes[counter.mcast] = counter.tx_bytes[0] - entry.last_txp_bin_tx_bytes_counter[counter.mcast]
                else:
                    entry.last_tx_bytes[counter.mcast] = counter.tx_bytes[0]
                entry.last_txp_bin_tx_bytes_counter[counter.mcast] = counter.tx_bytes[0]
                break


    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""
        for block in wtp.supports:
            if any(entry.block.hwaddr == block.hwaddr for entry in self.mcast_wtps):
                continue

            wtp_info = MCastWTPInfo()
            wtp_info.block = block
            wtp_info.mode = TX_MCAST_LEGACY_H
            self.mcast_wtps.append(wtp_info)

            self.txp_bin_counter(block=block,
                mcast=self.mcast_addr,
                callback=self.txp_bin_counter_callback,
                every=1000)


    def wtp_down_callback(self, wtp):
        """Called when a wtp connectdiss from the controller."""

        for index, entry in enumerate(self.mcast_wtps):
            for block in wtp.supports:
                if block.hwaddr == entry.block.hwaddr:
                    del self.mcast_wtps[index]
                    break


    def lvap_join_callback(self, lvap):
        """ New LVAP. """

        if any(lvap.addr == entry.addr for entry in self.mcast_clients):
            return

        default_block = next(iter(lvap.downlink))
        lvap_info = MCastClientInfo()

        lvap_info.addr = lvap.addr
        lvap_info.attached_hwaddr = default_block.hwaddr
        self.mcast_clients.append(lvap_info)

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == default_block.hwaddr:
                entry.attached_clients = entry.attached_clients + 1


    def lvap_leave_callback(self, lvap):
        """Called when an LVAP disassociates from a tennant."""

        default_block = next(iter(lvap.downlink))

        for index, entry in enumerate(self.mcast_wtps):
            if entry.block.hwaddr == default_block.hwaddr:
                entry.attached_clients = entry.attached_clients - 1

    def loop(self):
        """ Periodic job. """
        for index, entry in enumerate(self.mcast_wtps):
            tx_policy = entry.block.tx_policies[self.mcast_addr]
            tx_policy.mcast = TX_MCAST_LEGACY
            entry.mode = TX_MCAST_LEGACY_H
            tx_policy.mcs = [6]
            entry.rate[self.mcast_addr] = 6
    

    def to_dict(self):
        """Return JSON-serializable representation of the object."""
        out = super().to_dict()

        out['mcast_clients'] = []
        for p in self.mcast_clients:
            out['mcast_clients'].append(p.to_dict())
        out['mcast_wtps'] = []
        for p in self.mcast_wtps:
            out['mcast_wtps'].append(p.to_dict())
        out['mcast_addr'] = self.mcast_addr

        return out
                                    


def launch(tenant_id, every=1000, mcast_clients=[], mcast_wtps=[]):
    """ Initialize the module. """

    return McastLegacy(tenant_id=tenant_id, every=every, mcast_clients=mcast_clients, mcast_wtps=mcast_wtps)
