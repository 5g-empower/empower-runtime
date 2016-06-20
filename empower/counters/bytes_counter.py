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

"""Bytes counters module."""

from empower.counters.counters import PT_STATS_RESPONSE
from empower.counters.counters import STATS_RESPONSE
from empower.lvapp.lvappserver import ModuleLVAPPWorker
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
                    out[i] = out[i] + size * count
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
