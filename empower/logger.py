#!/usr/bin/env python3
#
# Copyright (c) 2016, Roberto Riggio
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
