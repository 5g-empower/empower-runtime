#!/usr/bin/env python3
#
# Copyright (c) 2019 Giovanni Baggio
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

"""InfluxDB stats sender."""


from tornado import gen
from concurrent.futures import ThreadPoolExecutor

from influxdb import InfluxDBClient

import empower.logger


class StatsSender:
    """InfluxDB client for sending the stats."""

    def __init__(self, influxdb_addr, influxdb_port,
                 influxdb_username, influxdb_password):

        self.log = empower.logger.get_logger()
        self.thread_pool = ThreadPoolExecutor(1)
        self.influxdb_client = InfluxDBClient(host=influxdb_addr,
                                              port=influxdb_port,
                                              username=influxdb_username,
                                              password=influxdb_password,
                                              timeout=3)
        # stats buffer, cannot rely on ThreadPoolExecutor because
        # it cannot clear pending jobs when shutdown is called
        self.stats = []
        self.busy = False

    @gen.coroutine
    def send_stat(self, **kwargs):

        if self.busy:
            # the sender thread is already working, buffer data
            self.stats.append(dict(**kwargs))
        else:
            self.busy = True
            error = yield self.thread_pool.submit(self._send_stat_worker,
                                                  **kwargs)
            self.busy = False

            if not error:
                self.log.info('Successfully sent stats to InfluxDB')
            else:
                self.log.warn('Failed to send stats to InfluxDB, %s' % error)
                # clear buffered stats
                self.stats.clear()

            if len(self.stats) > 0:
                # pop buffered data and send it
                self.send_stat(**self.stats.pop(0))

    def _send_stat_worker(self, **kwargs):

        try:
            # create database, it has no effect if it is already present
            self.influxdb_client.create_database(kwargs['database'])
            self.influxdb_client.write_points(**kwargs)
            return None
        except Exception as ex:
            return ex


def launch(influxdb_addr, influxdb_port=8086,
           influxdb_username='root', influxdb_password='root'):
    """Start InfluxdbClient Module. """

    stats_sender = StatsSender(influxdb_addr, influxdb_port,
                              influxdb_username, influxdb_password)

    return stats_sender
