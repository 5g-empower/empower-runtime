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

"""EmPOWER logging package."""

import inspect
import os
import logging

PATH = inspect.stack()[0][1]
EXT_PATH = PATH[0:PATH.rindex(os.sep)]
EXT_PATH = os.path.dirname(EXT_PATH) + os.sep
PATH = os.path.dirname(PATH) + os.sep


def get_logger(name=None, more_frames=0):
    """Logger factory."""

    if name is None:
        stack = inspect.stack()[1+more_frames]
        name = stack[1]
        if name.endswith('.py'):
            name = name[0:-3]
        elif name.endswith('.pyc'):
            name = name[0:-4]
        if name.startswith(PATH):
            name = name[len(PATH):]
        elif name.startswith(EXT_PATH):
            name = name[len(EXT_PATH):]
        name = name.replace('/', '.').replace('\\', '.')

        # Remove double names ("topology.topology" -> "topology")
        if name.find('.') != -1:
            toks = name.split('.')
            if len(toks) >= 2:
                if toks[-1] == toks[-2]:
                    del toks[-1]
                    name = '.'.join(toks)

        if name.startswith("ext."):
            name = name.split("ext.", 1)[1]

        if name.endswith(".__init__"):
            name = name.rsplit(".__init__", 1)[0]

    return logging.getLogger(name)
