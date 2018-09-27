#!/usr/bin/env python3
#
# Copyright (c) 2018 Giovanni Baggio

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

"""IBN Protocol Server."""

PT_VERSION = 0

# ryu to ctrl
PT_HELLO = "hello"

# ctrl to ryu
PT_UPDATE_ENDPOINT = "update_endpoint"
PT_REMOVE_ENDPOINT = "remove_endpoint"
PT_ADD_RULE = "add_rule"
PT_REMOVE_RULE = "remove_rule"
