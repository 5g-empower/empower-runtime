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

"""ACL unit tests."""


import unittest

from .common import BaseTest


class TestACLs(BaseTest):
    """ACL unit tests."""

    def test_add_acls(self):
        """test_add_acls."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f",
                    "04:46:65:49:e0:11",
                    "04:46:65:49:e0:11"
                ]
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("foo", "foo",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("bar", "bar",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f"
                ]
            }
        }

        params = \
            ("foo", "foo", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.put(params, data, 204)

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "puppa"
                ]
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.put(params, data, 400)

        self.delete(("foo", "foo",
                     "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

    def test_add_acls_invalid_creds(self):
        """test_add_acls_invalid_creds."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f",
                    "04:46:65:49:e0:11",
                    "04:46:65:49:e0:11"
                ]
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 201)

        self.get(("root", "root",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("foo", "foo",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        self.get(("bar", "bar",
                  "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 200)

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "allowed": [
                    "04:46:65:49:e0:1f"
                ]
            }
        }

        params = \
            ("bar", "bar", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.put(params, data, 401)

        params = \
            ("foo", "bar", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.put(params, data, 401)

        params = \
            ("foo", "foo", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.put(params, data, 204)


if __name__ == '__main__':
    unittest.main()
