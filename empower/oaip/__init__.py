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

""" OAI Server module. """

from construct import Sequence
from construct import Array
from construct import Struct
from construct import UBInt8
from construct import UBInt16
from construct import UBInt32
from construct import Bytes
from construct import Range
from construct import BitStruct
from construct import Bit
from construct import Padding


PT_VERSION = 0x00

PT_BYE = 0x00
PT_REGISTER = 0xFF
PT_HELLO = 0x01

HEADER = Struct("header", UBInt8("version"), UBInt8("type"), UBInt16("length"))

HELLO = Struct("hello", UBInt8("version"),
               UBInt8("type"),
               UBInt16("length"),
               UBInt32("seq"),
               UBInt32("period"),
               Bytes("wtp", 6),
               UBInt32("uplink_bytes"),
               UBInt32("downlink_bytes"),
               Bytes("ssid", lambda ctx: ctx.length - 26))


PT_TYPES = {PT_BYE: None,
            PT_REGISTER: None,
            PT_HELLO: HELLO}

PT_TYPES_HANDLERS = {PT_BYE: [],
                     PT_REGISTER: [],
                     PT_HELLO: []}
