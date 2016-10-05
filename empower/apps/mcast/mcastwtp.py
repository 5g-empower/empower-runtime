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

"""Multicast management app."""

import tornado.web
import tornado.httpserver
import time
import datetime
import sys

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.datatypes.etheraddress import EtherAddress
from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class MCastWTPInfo(object):
    def __init__(self):
        self.__block = None
        self.__last_txp_bin_counter = {} #dest_addr: counter
        self.__last_rx_pkts = {} #dest_addr: counter
        self.__rate = {} # {dest_addr:ewma_rate, dst_addr:ewma_rate...}
        self.__second_rate = {} # {dest_addr:curprob_rate, dest_addr:curprob_rate...}
        self.__prob_measurement = {}
        self.__last_rssi_change = None
        self.__attached_clients = 0

    @property
    def block(self):
        """Return the block of the object."""
        return self.__block

    @block.setter
    def block(self, block):

        self.__block = block

    @property
    def last_txp_bin_counter(self):
        """Return the total counter of the packets sent to a given address."""
        return self.__last_txp_bin_counter

    @last_txp_bin_counter.setter
    def last_txp_bin_counter(self, last_txp_bin_counter_info):

        self.__last_txp_bin_counter[list(last_txp_bin_counter_info.keys())[0]] = last_txp_bin_counter_info[list(last_txp_bin_counter_info.keys())[0]]

    @property
    def last_rx_pkts(self):
        """Return the last number of packets sent to a given address."""
        return self.__last_rx_pkts

    @last_rx_pkts.setter
    def last_rx_pkts(self, last_rx_pkts_info):

        self.__last_rx_pkts[list(last_rx_pkts_info.keys())[0]] = last_rx_pkts_info[list(last_rx_pkts_info.keys())[0]]

    @property
    def rate(self):
        """Return current multicast rate."""
        return self.__rate

    @rate.setter
    def rate(self, rate_info):

        self.__rate[list(rate_info.keys())[0]] = rate_info[list(rate_info.keys())[0]]

    @property
    def second_rate(self):
        """Return current multicast rate."""
        return self.__second_rate

    @second_rate.setter
    def second_rate(self, rate_info):
        if rate_info:
            self.__second_rate[list(rate_info.keys())[0]] = rate_info[list(rate_info.keys())[0]]

    @property
    def prob_measurement(self):
        """Return prob_measurement used."""
        return self.__prob_measurement

    @prob_measurement.setter
    def prob_measurement(self, prob_measurement_info):
        """Updates the probability used to calculate the new rate """
        self.__prob_measurement[list(prob_measurement_info.keys())[0]] = prob_measurement_info[list(prob_measurement_info.keys())[0]]

    @property
    def last_rssi_change(self):
        """Return the last_rssi_change that any client attached to this wtp did."""
        return self.__last_rssi_change

    @last_rssi_change.setter
    def last_rssi_change(self, last_rssi_change):

        self.__last_rssi_change = last_rssi_change

    @property
    def attached_clients(self):
        """Return the number of clients attached to this wtp."""
        return self.__attached_clients

    @attached_clients.setter
    def attached_clients(self, attached_clients):

        self.__attached_clients = attached_clients


    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        params = {}

        params['block'] = self.block.hwaddr
        params['last_txp_bin_counter'] = self.last_txp_bin_counter
        params['last_rx_pkts'] = self.last_rx_pkts
        params['rate'] = self.rate
        params['second_rate'] = self.second_rate
        params['prob_measurement'] = self.prob_measurement
        params['last_rssi_change'] = self.last_rssi_change
        params['attached_clients'] = self.attached_clients

        return params
