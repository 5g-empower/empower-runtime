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

"""Workers unit tests."""

import json
import unittest
import requests

from .common import BaseTest
from .common import URL


class TestWorkers(BaseTest):
    """Workers unit tests."""

    def test_register_new_worker(self):
        """test_register_new_worker."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", "/workers")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

    def test_register_existing_worker(self):
        """test_register_existing_worker."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", "/workers")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", loc)
        self.post(params, data, 400)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

    def test_register_new_worker_invalid_creds(self):
        """test_register_new_worker_invalid_creds."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("foo", "foo", "/workers")
        self.post(params, data, 401)

        params = ("root", "foo", "/workers")
        self.post(params, data, 401)

    def test_modify_worker_invalid_param_name(self):
        """test_modify_worker_invalid_param_name."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", "/workers")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        data = {
            "params": {
                "puppa": 2000
            }
        }

        params = ("root", "root", loc)
        self.put(params, data, 404)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

    def test_modify_worker_param(self):
        """test_modify_worker_param."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", "/workers")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        data = {
            "params": {
                "every": 5000
            }
        }

        params = ("root", "root", loc)
        self.put(params, data, 204)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

    def test_modify_app_invalid_param_value(self):
        """test_modify_app_invalid_param_value."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", "/workers")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        data = {
            "params": {
                "every": "puppa"
            }
        }

        params = ("root", "root", loc)
        self.put(params, data, 400)

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

    def test_modify_worker_attribute(self):
        """test_modify_worker_attribute."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", "/workers")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc + "/channel_stats")
        self.get(params, 200)

        data = {
            "value": "null value"
        }

        params = ("root", "root", loc + "/channel_stats")
        self.put(params, data, 204)

        params = ("root", "root", loc + "/channel_stats")
        resp = self.get(params, 200)

        req = requests.get(url=URL % ("root", "root", loc + "/channel_stats"))
        text = json.loads(req.text)
        self.assertEqual(text[0], "null value")

        data = {
            "value": {}
        }

        params = ("root", "root", loc + "/channel_stats")
        self.put(params, data, 204)

        params = ("root", "root", loc + "/channel_stats")
        resp = self.get(params, 200)

        req = requests.get(url=URL % ("root", "root", loc + "/channel_stats"))
        text = json.loads(req.text)
        self.assertEqual(text[0], {})

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

    def test_modify_invalid_worker_attribute(self):
        """test_modify_invalid_worker_attribute."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        params = ("root", "root", "/workers")
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc + "/invalid")
        self.get(params, 404)

        data = {
            "value": "null value"
        }

        params = ("root", "root", loc + "/invalid")
        self.put(params, data, 404)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)


if __name__ == '__main__':
    unittest.main()
