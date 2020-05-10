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

import unittest

from .common import BaseTest


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

    def test_register_new_worker_fixed_uuid(self):
        """test_register_new_worker."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        url = "/workers/7f372516-d650-46ea-8db4-8f079a844dc5"
        params = ("root", "root", url)
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", url)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

    def test_register_new_worker_duplicate_no_uuid(self):
        """test_register_new_worker."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
            "params": {
                "every": 1000
            }
        }

        url = "/workers"
        params = ("root", "root", url)

        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        resp = self.post(params, data, 201)
        loc2 = resp.headers['Location'].replace("/api/v1", "")

        self.assertEqual(loc, loc2)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc2)
        self.delete(params, 404)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = ("root", "root", loc2)
        self.get(params, 404)

    def test_register_new_worker_different_params(self):
        """test_register_new_worker."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
            "params": {
                "every": 1000
            }
        }

        url = "/workers"
        params = ("root", "root", url)

        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
            "params": {
                "every": 2000
            }
        }

        resp = self.post(params, data, 201)
        loc2 = resp.headers['Location'].replace("/api/v1", "")

        self.assertNotEqual(loc, loc2)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc2)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = ("root", "root", loc2)
        self.get(params, 404)

    def test_register_new_worker_duplicate_uuid(self):
        """test_register_new_worker."""

        self.get(("root", "root", "/workers"), 200)

        data = {
            "name": "empower.workers.wifichannelstats.wifichannelstats",
        }

        url = "/workers/7f372516-d650-46ea-8db4-8f079a844dc5"
        params = ("root", "root", url)
        resp = self.post(params, data, 201)
        loc = resp.headers['Location'].replace("/api/v1", "")

        url = "/workers/7f372516-d650-46ea-8db4-8f079a844dd5"
        params = ("root", "root", url)
        resp = self.post(params, data, 201)
        loc2 = resp.headers['Location'].replace("/api/v1", "")

        self.assertNotEqual(loc, loc2)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc2)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)

        params = ("root", "root", loc2)
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

    def test_modify_worker_invalid_param_value(self):
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

    def test_add_callback(self):
        """test_add_callback."""

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
            "version": "1.0",
            "name": "default",
            "callback": "http://www.domain.io/resource",
            "callback_type": "rest"
        }

        params = ("root", "root", loc + "/callbacks")
        self.post(params, data, 201)

        loc = resp.headers['Location'].replace("/api/v1", "")

        params = ("root", "root", loc)
        self.get(params, 200)

        params = ("root", "root", loc)
        self.delete(params, 204)

        params = ("root", "root", loc)
        self.get(params, 404)


if __name__ == '__main__':
    unittest.main()
