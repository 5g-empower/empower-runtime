#!/usr/bin/env python3
#
# Copyright (c) 2017, Estefanía Coronado
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

"""Multicast client info."""


class MCastClientInfo(object):

    def __init__(self, addr):
        self.addr = addr
        self.best_prob = None
        self.best_rate = None
        self.valid_rates = None

        self.rssi = 0
        self.attached_hwaddr = None
        self.rx_pkts = {}
        self.rates = {}
        self.higher_thershold_ewma_rates = []
        self.higher_thershold_cur_prob_rates = []
        self.highest_rate = 0
        self.highest_cur_prob_rate = 0

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = {}

        out['addr'] = self.addr
        out['best_prob'] = self.best_prob
        out['best_rate'] = self.best_rate
        out['valid_rates'] = self.valid_rates

        return out
