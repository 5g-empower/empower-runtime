#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

""" LVNFP Server module. """

PT_VERSION = 0

# ctrl to self
PT_BYE = "bye"
PT_REGISTER = "register"
PT_LVNF_JOIN = "lvnf_join"
PT_LVNF_LEAVE = "lvnf_leave"

# cpp to ctrl
PT_HELLO = "hello"
PT_CAPS_RESPONSE = "caps_response"
PT_LVNF_STATUS_RESPONSE = "lvnf_status_response"
PT_ADD_LVNF_RESPONSE = "add_lvnf_response"
PT_DEL_LVNF_RESPONSE = "del_lvnf_response"

# ctrl to cpp
PT_LVNF_STATUS_REQUEST = "lvnf_status_request"
PT_CAPS_REQUEST = "caps_request"
PT_ADD_LVNF = "add_lvnf"
PT_DEL_LVNF = "del_lvnf"

# maps types with parsers
PT_TYPES = {}
PT_TYPES[PT_BYE] = None
PT_TYPES[PT_REGISTER] = None
PT_TYPES[PT_HELLO] = None
PT_TYPES[PT_CAPS_REQUEST] = None
PT_TYPES[PT_CAPS_RESPONSE] = None
PT_TYPES[PT_ADD_LVNF] = None
PT_TYPES[PT_DEL_LVNF] = None
PT_TYPES[PT_LVNF_STATUS_REQUEST] = None
PT_TYPES[PT_ADD_LVNF_RESPONSE] = None
PT_TYPES[PT_DEL_LVNF_RESPONSE] = None
PT_TYPES[PT_LVNF_STATUS_RESPONSE] = None

# maps types with secondary handlers
PT_TYPES_HANDLERS = {}
PT_TYPES_HANDLERS[PT_BYE] = []
PT_TYPES_HANDLERS[PT_REGISTER] = []
PT_TYPES_HANDLERS[PT_LVNF_JOIN] = []
PT_TYPES_HANDLERS[PT_LVNF_LEAVE] = []
PT_TYPES_HANDLERS[PT_HELLO] = []
PT_TYPES_HANDLERS[PT_CAPS_REQUEST] = []
PT_TYPES_HANDLERS[PT_CAPS_RESPONSE] = []
PT_TYPES_HANDLERS[PT_ADD_LVNF] = []
PT_TYPES_HANDLERS[PT_DEL_LVNF] = []
PT_TYPES_HANDLERS[PT_LVNF_STATUS_REQUEST] = []
PT_TYPES_HANDLERS[PT_ADD_LVNF_RESPONSE] = []
PT_TYPES_HANDLERS[PT_DEL_LVNF_RESPONSE] = []
PT_TYPES_HANDLERS[PT_LVNF_STATUS_RESPONSE] = []
