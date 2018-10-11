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

"""EmPOWER Schema validator."""

import tornado


def _parse_schema(schema, data):

    params = {}

    for key in schema:

        mandatory = schema[key]["mandatory"]

        if mandatory and key not in data:
            msg = "Missing parameter (%s)" % key
            raise ValueError(msg)
        elif key not in data:
            continue
        else:
            if isinstance(schema[key]["type"], dict):
                params[key] = _parse_schema(schema[key]["type"], data[key])
            else:
                arg_type = schema[key]["type"]
                param = arg_type(data[key])
                params[key] = param

    return params


def validate(returncode=200, min_args=0, max_args=0, input_schema=None):
    """Validate REST method."""

    def decorator(func):

        def magic(self, *args):

            try:

                if len(args) < min_args or len(args) > max_args:
                    msg = "Invalid url (%u, %u)" % (min_args, max_args)
                    raise ValueError(msg)

                params = {}

                if input_schema:
                    request = tornado.escape.json_decode(self.request.body)
                    params = _parse_schema(input_schema, request)

                output = func(self, *args, **params)

                if returncode == 200:
                    self.write_as_json(output)

            except KeyError as ex:
                self.send_error(404, message=ex)

            except ValueError as ex:
                self.send_error(400, message=ex)

            except AttributeError as ex:
                self.send_error(400, message=ex)

            except TypeError as ex:
                self.send_error(400, message=ex)

            self.set_status(returncode, None)

        magic.__doc__ = func.__doc__

        return magic

    return decorator
