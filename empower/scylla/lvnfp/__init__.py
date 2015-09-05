#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
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
PT_STATUS_LVNF = "status_lvnf"

# ctrl to cpp
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
PT_TYPES[PT_STATUS_LVNF] = None

# maps types with secondary handlers
PT_TYPES_HANDLERS = {}
PT_TYPES_HANDLERS[PT_BYE] = []
PT_TYPES_HANDLERS[PT_REGISTER] = []
PT_TYPES_HANDLERS[PT_HELLO] = []
PT_TYPES_HANDLERS[PT_CAPS_REQUEST] = []
PT_TYPES_HANDLERS[PT_CAPS_RESPONSE] = []
PT_TYPES_HANDLERS[PT_ADD_LVNF] = []
PT_TYPES_HANDLERS[PT_DEL_LVNF] = []
PT_TYPES_HANDLERS[PT_STATUS_LVNF] = []
