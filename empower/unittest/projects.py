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

"""Projects unit tests."""


import unittest

from .common import BaseTest


class TestProjects(BaseTest):
    """Projects unit tests."""

    def test_simple_gets(self):
        """test_simple_gets"""

        self.get(("root", "root", "/projects"), 200)

    def test_create_new_project(self):
        """test_create_new_project"""

        data = {
            "desc": "Test project",
            "owner": "foo",
            "wifi_props": {"invalid_field": 1}
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 400)

        data = {
            "version": "1.0",
            "desc": "Test project",
            "owner": "foo",
            "lte_props": {"invalid_field": 1}
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 400)

        data = {
            "version": "1.0",
            "desc": "Test project",
            "owner": "foo"
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

        self.delete(("foo", "foo",
                     "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

    def test_create_wifi_project(self):
        """test_create_wifi_project"""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "bssid_type": "unique"
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

        self.delete(("foo", "foo",
                     "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

    def test_create_wifi_project_default_bssid_type(self):
        """test_create_wifi_project_default_bssid_type."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER"
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

        self.delete(("foo", "foo",
                     "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

    def test_create_wifi_project_wrong_bssid_type(self):
        """test_create_wifi_project_wrong_bssid_type."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "wifi_props": {
                "ssid": "EmPOWER",
                "bssid_type": "wrong"
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 400)

    def test_create_lte_project(self):
        """test_create_lte_project."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "lte_props": {
                "plmnid": "222f93"
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

        self.delete(("foo", "foo",
                     "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26"), 204)

    def test_create_lte_project_wrong_plmnid(self):
        """test_create_lte_project_wrong_plmnid."""

        data = {
            "owner": "foo",
            "desc": "Test project",
            "lte_props": {
                "plmnid": "wrong plmnid"
            }
        }

        params = \
            ("root", "root", "/projects/52313ecb-9d00-4b7d-b873-b55d3d9ada26")
        self.post(params, data, 400)


if __name__ == '__main__':
    unittest.main()
