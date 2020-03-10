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
import types

from functools import singledispatch


@singledispatch
def serialize(obj):
    """Recursively serialise objects."""

    return obj


@serialize.register(types.FunctionType)
@serialize.register(types.MethodType)
def _(obj):
    return obj.__name__


@serialize.register(dict)
def _(obj):
    return {str(k): serialize(v) for k, v in obj.items()}


@serialize.register(list)
@serialize.register(set)
@serialize.register(tuple)
def _(obj):
    return [serialize(v) for v in obj]


@serialize.register(datetime.datetime)
@serialize.register(uuid.UUID)
@serialize.register(ipaddress.IPv4Address)
def _(obj):
    return str(obj)


def serializable_string(cls):
    """Decorator for classes that can be serialized as dicts."""

    def decorator(cls):

        @serialize.register(cls)
        def _(obj):
            return str(obj)

        return cls

    return decorator(cls)


def serializable_dict(cls):
    """Decorator for classes that can be serialized as dicts."""

    def decorator(cls):

        @serialize.register(cls)
        def _(obj):
            return serialize(obj.to_dict())

        return cls

    return decorator(cls)
