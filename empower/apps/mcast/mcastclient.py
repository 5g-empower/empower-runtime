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

from empower.main import RUNTIME

import empower.logger
LOG = empower.logger.get_logger()


class MCastClientInfo(object):
	def __init__(self):
		self.__addr = None
		self.__rssi = 0 # rssi of the current block attached to
		self.__attached_hwaddr = None
		self.__rx_pkts = dict() # dst_addr: rx_pkts
		self.__rates = dict() 
		self.__wtps = dict() # ap/block: rssi
		self.__higher_thershold_ewma_rates = []
		self.__higher_thershold_cur_prob_rates = []
		self.__highest_rate = 0
		self.__highest_cur_prob_rate = 0
		self.__last_unsuccessful_handover = dict()
		self.__last_handover_time = None

	@property
	def addr(self):
		"""Return the lvap_addr of the client."""
		return self.__addr

	@addr.setter
	def addr(self, addr):
		self.__addr = addr

	@property
	def rssi(self):
		"""Return the rssi perceived from the wtp currenty attached to."""
		return self.__rssi

	@rssi.setter
	def rssi(self, rssi):
		self.__rssi = rssi

	@property
	def attached_hwaddr(self):
		"""Return the hwaddr of the wtp currenty attached to."""
		return self.__attached_hwaddr

	@attached_hwaddr.setter
	def attached_hwaddr(self, attached_hwaddr):
		self.__attached_hwaddr = attached_hwaddr

	@property
	def rx_pkts(self):
		"""Return the number of packets received from a given address"""
		return self.__rx_pkts

	@rx_pkts.setter
	def rx_pkts(self, rx_pkts_info):
		self.__rx_pkts = rx_pkts_info

	@property
	def rates(self):
		"""Return the number of packets received from a given address"""
		return self.__rates

	@rates.setter
	def rates(self, rates_info):
		self.__rates = rates_info

	@property
	def wtps(self):
		"""Return the rssi of the wtps that are holding the tenant that this client is attached to"""
		return self.__wtps

	@wtps.setter
	def wtps(self, wtps_info):
		self.__wtps.clear()
		self.__wtps = wtps_info

	@property
	def higher_thershold_ewma_rates(self):
		"""Return the rates that offer a emwa probability higher than a thershold"""
		return self.__higher_thershold_ewma_rates

	@higher_thershold_ewma_rates.setter
	def higher_thershold_ewma_rates(self, higher_thershold_ewma_rates_info):
		self.__higher_thershold_ewma_rates = higher_thershold_ewma_rates_info

	@property
	def higher_thershold_cur_prob_rates(self):
		"""Return the rates that offer a cur probability higher than a thershold"""
		return self.__higher_thershold_cur_prob_rates

	@higher_thershold_cur_prob_rates.setter
	def higher_thershold_cur_prob_rates(self, higher_thershold_cur_prob_rates_info):
		self.__higher_thershold_cur_prob_rates = higher_thershold_cur_prob_rates_info

	@property
	def highest_rate(self):
		"""Return the best rate for this client regarding ewma prob."""
		return self.__highest_rate

	@highest_rate.setter
	def highest_rate(self, highest_rate):
		self.__highest_rate = highest_rate

	@property
	def highest_cur_prob_rate(self):
		"""Return the second best rate for this client regarding cur prob."""
		return self.__highest_cur_prob_rate

	@highest_cur_prob_rate.setter
	def highest_cur_prob_rate(self, highest_cur_prob_rate):
		self.__highest_cur_prob_rate = highest_cur_prob_rate

	@property
	def last_unsuccessful_handover(self):
		"""Return the last_unsuccessful_handover done."""
		return self.__last_unsuccessful_handover

	@last_unsuccessful_handover.setter
	def last_unsuccessful_handover(self, last_unsuccessful_handover):
		self.__last_unsuccessful_handover = last_unsuccessful_handover

	@property
	def last_handover_time(self):
		"""Return the time of the handover done."""
		return self.__last_handover_time

	@last_handover_time.setter
	def last_handover_time(self, last_handover_time):
		self.__last_handover_time = last_handover_time


	def to_dict(self):
		"""Return JSON-serializable representation of the object."""

		params = {}
		wtps = {str(k): v for k, v in self.wtps.items()}
		rx_pkts = {str(k): v for k, v in self.rx_pkts.items()}
		last_unsuccessful_handover = {str(k): v for k, v in self.last_unsuccessful_handover.items()}

		params['addr'] = self.addr
		params['rssi'] = self.rssi
		params['attached_hwaddr'] = self.attached_hwaddr
		params['rx_pkts'] = rx_pkts
		params['rates'] = self.rates
		params['wtps'] = wtps
		params['higher_thershold_ewma_rates'] = self.higher_thershold_ewma_rates
		params['higher_thershold_cur_prob_rates'] = self.higher_thershold_cur_prob_rates
		params['highest_rate'] = self.highest_rate
		params['highest_cur_prob_rate'] = self.highest_cur_prob_rate
		params['last_unsuccessful_handover'] = last_unsuccessful_handover
		params['last_handover_time'] = self.last_handover_time

		return params