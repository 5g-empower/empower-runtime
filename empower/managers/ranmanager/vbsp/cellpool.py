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

"""EmPOWER cell pool and cell classes."""

from empower_core.serialize import serializable_dict


class CellPool(list):
    """Cell pool.

    Extends the list in order to add a few filtering and sorting methods
    """

    def sort_by_rsrp(self, ue_id):
        """Return list sorted by rsrp for the specified address."""

        filtered = [x for x in self if ue_id in x.ue_measurements]

        cells = sorted(filtered,
                       key=lambda x: x.ue_measurements[ue_id]['rsrp'],
                       reverse=True)

        return CellPool(cells)

    def sort_by_rsrq(self, ue_id):
        """Return list sorted by rsrq for the specified address."""

        filtered = [x for x in self if ue_id in x.ue_measurements]

        cells = sorted(filtered,
                       key=lambda x: x.ue_measurements[ue_id]['rsrq'],
                       reverse=True)

        return CellPool(cells)

    def first(self):
        """Return first entry in the list."""

        if self:
            cell = list.__getitem__(self, 0)
            return cell

        return None

    def last(self):
        """Return last entry in the list."""

        if self:
            cell = list.__getitem__(self, -1)
            return cell

        return None


@serializable_dict
class Cell:
    """An LTE eNB cell.

    Attributes:
        vbs: The VBS at which this cell is available
        pci: the physical cell id
        dl_earfcn: downlink center frequency
        dl_bandwidth: downlink bandwidth
        ul_earfcn: uplink center frequency
        ul_bandwidth: uplink bandwidth
        ue_measurements: UE measurements (RSRP/RSRQ)
        cell_measurements: cell measurements
    """

    def __init__(self, vbs, pci, dl_earfcn, ul_earfcn, n_prbs):
        self.vbs = vbs
        self.pci = pci
        self.dl_earfcn = dl_earfcn
        self.ul_earfcn = ul_earfcn
        self.n_prbs = n_prbs
        self.mac_prb_utilization = {}

    def to_str(self):
        """Return an ASCII representation of the object."""

        return "vbs %s pci %u dl_earfcn %u dl_earfcn %u n_prbs %u" % \
            (self.vbs.addr, self.pci, self.dl_earfcn, self.ul_earfcn,
             self.n_prbs)

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.__class__.__name__ + "('" + self.to_str() + "')"

    def __hash__(self):
        return hash(self.vbs) + hash(self.pci)

    def __eq__(self, other):
        if isinstance(other, Cell):
            return self.vbs == other.vbs and self.pci == other.pci
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        out = {}

        out['addr'] = self.vbs.addr
        out['pci'] = self.pci
        out['dl_earfcn'] = self.dl_earfcn
        out['ul_earfcn'] = self.ul_earfcn
        out['n_prbs'] = self.n_prbs
        out['mac_prb_utilization'] = self.mac_prb_utilization

        return out
