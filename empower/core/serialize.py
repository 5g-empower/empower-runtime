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

"""JSON Serializer."""

import uuid
import ipaddress
import datetime

from functools import singledispatch

import empower.core.service as service
import empower.core.etheraddress as etheraddress
import empower.core.ssid as ssid
import empower.core.plmnid as plmnid
import empower.core.wtp as wtp
import empower.core.vbs as vbs
import empower.core.lvap as lvap
import empower.core.resourcepool as resourcepool
import empower.core.txpolicy as txpolicy
import empower.managers.ranmanager.ranconnection as ranconnection
import empower.managers.accountsmanager.account as account
import empower.managers.projectsmanager.project as project
import empower.managers.envmanager.env as env


@singledispatch
def serialize(obj):
    """Recursively serialise objects."""

    return obj


@serialize.register(dict)
def _(obj):
    return {str(k): serialize(v) for k, v in obj.items()}


@serialize.register(list)
@serialize.register(set)
@serialize.register(tuple)
def _(obj):
    return [serialize(v) for v in obj]


@serialize.register(service.EService)
@serialize.register(account.Account)
@serialize.register(project.Project)
@serialize.register(env.Env)
@serialize.register(project.WiFiSlice)
@serialize.register(project.LTESlice)
@serialize.register(wtp.WTP)
@serialize.register(vbs.VBS)
@serialize.register(lvap.LVAP)
@serialize.register(resourcepool.ResourceBlock)
@serialize.register(txpolicy.TxPolicy)
@serialize.register(ranconnection.RANConnection)
def _(obj):
    return serialize(obj.to_dict())


@serialize.register(datetime.datetime)
@serialize.register(uuid.UUID)
@serialize.register(ssid.SSID)
@serialize.register(plmnid.PLMNID)
@serialize.register(etheraddress.EtherAddress)
@serialize.register(ipaddress.IPv4Address)
def _(obj):
    return str(obj)
