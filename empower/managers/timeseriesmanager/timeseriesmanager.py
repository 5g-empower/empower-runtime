#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""Time series manager."""

from concurrent.futures import ThreadPoolExecutor

from tornado import gen
from influxdb import InfluxDBClient

from empower.core.service import EService
from empower.core.serialize import serialize

DEFAULT_DATABASE = "empower"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8086
DEFAULT_USERNAME = "root"
DEFAULT_PASSWORD = "password"


class TimeSeriesManager(EService):
    """Time series manager."""

    def __init__(self, **kwargs):

        if 'database' not in kwargs:
            kwargs['database'] = DEFAULT_DATABASE

        if 'host' not in kwargs:
            kwargs['host'] = DEFAULT_HOST

        if 'port' not in kwargs:
            kwargs['port'] = DEFAULT_PORT

        if 'username' not in kwargs:
            kwargs['username'] = DEFAULT_USERNAME

        if 'password' not in kwargs:
            kwargs['password'] = DEFAULT_PASSWORD

        super().__init__(**kwargs)

        self.thread_pool = None
        self.influxdb_client = None

        # stats buffer, cannot rely on ThreadPoolExecutor because
        # it cannot clear pending jobs when shutdown is called
        self.stats = []
        self.busy = False

    def start(self):
        """Start time series manager manager."""

        super().start()

        self.thread_pool = ThreadPoolExecutor(1)
        self.influxdb_client = InfluxDBClient(host=self.host,
                                              port=self.port,
                                              username=self.username,
                                              password=self.password,
                                              timeout=3,
                                              database=self.database)

        # create database, it has no effect if it is already present
        self.influxdb_client.create_database(self.database)

        self.log.info("Connected to InfluxDB database %s", self.database)

    @property
    def database(self):
        """Return database."""

        return self.params["database"]

    @database.setter
    def database(self, value):
        """Set database."""

        self.params["database"] = value

    @property
    def host(self):
        """Return host."""

        return self.params["host"]

    @host.setter
    def host(self, value):
        """Set host."""

        self.params["host"] = value

    @property
    def port(self):
        """Return port."""

        return self.params["port"]

    @port.setter
    def port(self, value):
        """Set port."""

        self.params["port"] = int(value)

    @property
    def username(self):
        """Return username."""

        return self.params["username"]

    @username.setter
    def username(self, value):
        """Set username."""

        self.params["username"] = value

    @property
    def password(self):
        """Return password."""

        return self.params["password"]

    @password.setter
    def password(self, value):
        """Set password."""

        self.params["password"] = value

    @gen.coroutine
    def write_points(self, points):
        """Add new points to the DB."""

        # the sender thread is already working, buffer data
        if self.busy:
            self.stats.append(points)
            return

        self.busy = True

        error = yield self.thread_pool.submit(self.__write_points_worker,
                                              points)
        self.busy = False

        # clear buffer in case of error
        if error:
            self.stats.clear()

        # pop buffered data and send it
        if self.stats:
            self.write_points(self.stats.pop(0))

    def __write_points_worker(self, points):

        try:
            self.influxdb_client.write_points(points=serialize(points))
        except Exception as ex:
            self.log.exception(ex)
            return False

        return True


def launch(**kwargs):
    """Start the time series manager. """

    return TimeSeriesManager(**kwargs)
