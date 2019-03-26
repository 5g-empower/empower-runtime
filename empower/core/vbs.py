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

"""Virtual Base Station Point."""

from empower.core.pnfdev import BasePNFDev


class VBS(BasePNFDev):
    """A Virtual Base Station Point.

    Attributes:
        addr: This PNFDev MAC address (EtherAddress)
        label: A human-radable description of this PNFDev (str)
        connection: Signalling channel connection (BasePNFPMainHandler)
        last_seen: Sequence number of the last hello message received (int)
        last_seen_ts: Timestamp of the last hello message received (int)
        seq: Next sequence number (int)
        period: update period (in ms)
        datapath: the associated OF switch
        state: this device status
        log: logging facility
    """

    ALIAS = "vbses"

    def __init__(self, addr, label):
        super().__init__(addr, label)
        self.cells = {}

    def cells(self):
        """Return all cells supported by this VBS."""

        pool = CellPool()

        # Update the pool with all the available cells
        for cell in self.cells.values():
            pool.append(cell)

        return pool

    def to_dict(self):
        """Return a JSON-serializable dictionary representing the VBS."""

        out = super().to_dict()
        out['cells'] = self.cells
        return out
