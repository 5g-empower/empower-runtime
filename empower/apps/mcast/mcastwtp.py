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

"""Multicast WTP info."""

from empower.core.resourcepool import TX_MCAST_DMS
from empower.core.resourcepool import TX_MCAST_LEGACY
from empower.core.resourcepool import TX_MCAST_DMS_H
from empower.core.resourcepool import TX_MCAST_LEGACY_H


class MCastWTPInfo:

    def __init__(self, block):
        self.block = block
        self.mode = TX_MCAST_DMS_H
        self.last_txp_bin_tx_pkts_counter = {}
        self.last_tx_pkts = {}
        self.last_txp_bin_tx_bytes_counter = {}
        self.last_tx_bytes = {}
        self.rate = {}
        self.cur_prob_rate = {}
        self.last_rssi_change = 0
        self.last_prob_update = 0
        self.attached_clients = 0
        self.dms_max_period = 1
        self.legacy_max_period = 3
        self.current_period = 0
        self.attached_clients_rssi = {}
        self.avg_perceived_rssi = 0
        self.dev_perceived_rssi = 0

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = {}

        out['block'] = self.block
        out['attached_clients'] = self.attached_clients

        return out
