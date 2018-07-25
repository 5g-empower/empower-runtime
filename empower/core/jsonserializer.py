#!/usr/bin/env python3
#
# Copyright (c) 2018 Roberto Riggio
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

"""EmPOWER Runtime JSON Serializer."""

import json
import uuid
import types
import ipaddress

import empower.datatypes.etheraddress
import empower.datatypes.ssid
import empower.datatypes.plmnid
import empower.datatypes.dpid
import empower.datatypes.dscp
import empower.datatypes.match


class IterEncoder(json.JSONEncoder):
    """Encode iterable objects as lists."""

    def default(self, obj):

        try:
            return list(obj)
        except TypeError:
            return super().default(obj)


class EmpowerEncoder(IterEncoder):
    """Handle the representation of the EmPOWER datatypes in JSON format."""

    def default(self, obj):

        if isinstance(obj, (types.FunctionType, types.MethodType)):
            return obj.__name__

        instances = (uuid.UUID,
                     ipaddress.IPv4Address,
                     empower.datatypes.dscp.DSCP,
                     empower.datatypes.ssid.SSID,
                     empower.datatypes.plmnid.PLMNID,
                     empower.datatypes.etheraddress.EtherAddress,
                     empower.datatypes.dpid.DPID,
                     empower.datatypes.match.Match)

        if isinstance(obj, instances):
            return str(obj)

        if hasattr(obj, 'to_dict'):
            return obj.to_dict()

        if hasattr(obj, 'isoformat'):
            return obj.isoformat()

        return super().default(obj)
