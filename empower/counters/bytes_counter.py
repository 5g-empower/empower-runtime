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

"""Bytes counters module."""

from empower.counters.counters import PT_STATS_RESPONSE
from empower.counters.counters import STATS_RESPONSE
from empower.core.module import ModuleLVAPPWorker
from empower.counters.counters import Counter
from empower.core.lvap import LVAP

from empower.main import RUNTIME


class BytesCounter(Counter):
    """ Stats returning byte counters """

    MODULE_NAME = "bytes_counter"

    def fill_samples(self, data):
        """ Compute samples.

        Samples are in the following format (after ordering):

        [[60, 3], [66, 2], [74, 1], [98, 40], [167, 2], [209, 2], [1466, 1762]]

        Each 2-tuple has format [ size, count ] where count is the number of
        size-long (bytes, including the Ethernet 2 header) TX/RX by the LVAP.

        """

        samples = sorted(data, key=lambda entry: entry[0])
        out = [0] * len(self.bins)

        for entry in samples:
            if len(entry) == 0:
                continue
            size = entry[0]
            count = entry[1]
            for i in range(0, len(self.bins)):
                if size <= self.bins[i]:
                    out[i] = out[i] + count
                    break

        return out


class BytesCounterWorker(ModuleLVAPPWorker):
    """Bytes counts worker."""

    pass


def bytes_counter(**kwargs):
    """Create a new module."""

    worker = RUNTIME.components[BytesCounterWorker.__module__]
    return worker.add_module(**kwargs)


def bound_bytes_counter(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    kwargs['lvap'] = self.addr
    return bytes_counter(**kwargs)

setattr(LVAP, BytesCounter.MODULE_NAME, bound_bytes_counter)


def launch():
    """ Initialize the module. """

    return BytesCounterWorker(BytesCounter, PT_STATS_RESPONSE, STATS_RESPONSE)
