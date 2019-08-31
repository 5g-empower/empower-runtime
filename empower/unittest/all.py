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

"""Full unit test suite."""

import unittest
from .projects import TestProjects
from .accounts import TestAccounts
from .acls import TestACLs
from .wtps import TestWTPs
from .vbses import TestVBSes
from .wifislices import TestWiFiSlices
from .lteslices import TestLTESlices
from .applications import TestApplications
from .workers import TestWorkers


def full_suite():
    """Full unit test suite."""

    suite = unittest.TestSuite()

    suite.addTest(TestWorkers('test_register_new_worker'))
    suite.addTest(TestWorkers('test_register_new_worker_invalid_creds'))
    suite.addTest(TestWorkers('test_register_existing_worker'))
    suite.addTest(TestWorkers('test_modify_worker_invalid_param_name'))
    suite.addTest(TestWorkers('test_modify_worker_param'))
    suite.addTest(TestWorkers('test_modify_app_invalid_param_value'))
    suite.addTest(TestWorkers('test_modify_worker_attribute'))
    suite.addTest(TestWorkers('test_modify_invalid_worker_attribute'))

    suite.addTest(TestAccounts('test_simple_gets'))
    suite.addTest(TestAccounts('test_create_existing_user'))
    suite.addTest(TestAccounts('test_create_new_user'))
    suite.addTest(TestAccounts('test_update_user_details'))
    suite.addTest(TestAccounts('test_credentials'))

    suite.addTest(TestProjects('test_simple_gets'))
    suite.addTest(TestProjects('test_create_new_project'))
    suite.addTest(TestProjects('test_create_wifi_project'))
    suite.addTest(TestProjects('test_create_wifi_project_default_bssid_type'))
    suite.addTest(TestProjects('test_create_wifi_project_wrong_bssid_type'))
    suite.addTest(TestProjects('test_create_lte_project'))
    suite.addTest(TestProjects('test_create_lte_project_wrong_plmnid'))

    suite.addTest(TestACLs('test_add_acls'))
    suite.addTest(TestACLs('test_add_acls_invalid_creds'))

    suite.addTest(TestWTPs('test_create_new_device_empty_body'))
    suite.addTest(TestWTPs('test_create_new_device_wrong_address'))
    suite.addTest(TestWTPs('test_create_new_device'))
    suite.addTest(TestWTPs('test_create_new_device_custom_desc'))

    suite.addTest(TestVBSes('test_create_new_device_empty_body'))
    suite.addTest(TestVBSes('test_create_new_device_wrong_address'))
    suite.addTest(TestVBSes('test_create_new_device'))
    suite.addTest(TestVBSes('test_create_new_device_custom_desc'))

    suite.addTest(TestWiFiSlices('test_create_new_wifi_slice'))
    suite.addTest(TestWiFiSlices('test_create_new_wifi_slice_after_prj'))
    suite.addTest(TestWiFiSlices('test_update_wifi_slice'))
    suite.addTest(TestWiFiSlices('test_delete_default_wifi_slice'))

    suite.addTest(TestLTESlices('test_create_new_lte_slice'))
    suite.addTest(TestLTESlices('test_create_new_lte_slice_after_prj'))
    suite.addTest(TestLTESlices('test_update_lte_slice'))
    suite.addTest(TestLTESlices('test_delete_default_lte_slice'))

    suite.addTest(TestApplications('test_register_new_app'))
    suite.addTest(TestApplications('test_register_existing_app_invalid_creds'))
    suite.addTest(TestApplications('test_register_existing_app'))
    suite.addTest(TestApplications('test_modify_app_invalid_param_name'))
    suite.addTest(TestApplications('test_modify_app_param'))
    suite.addTest(TestApplications('test_modify_app_invalid_param_value'))

    return suite


if __name__ == '__main__':
    unittest.TextTestRunner().run(full_suite())
