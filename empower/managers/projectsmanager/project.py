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

"""Project Class."""

from pymodm import fields, EmbeddedMongoModel
from pymodm.errors import ValidationError

import empower.core.serialize as serialize
from empower.managers.envmanager.env import Env
from empower.core.slice import WiFiSlice, LTESlice
from empower.core.etheraddress import EtherAddress
from empower.core.etheraddress import EtherAddressField
from empower.core.plmnid import PLMNIDField
from empower.core.ssid import SSIDField

T_BSSID_TYPE_SHARED = "shared"
T_BSSID_TYPE_UNIQUE = "unique"
T_BSSID_TYPE_TYPES = [T_BSSID_TYPE_SHARED, T_BSSID_TYPE_UNIQUE]

T_STA_SCHED_RR = 0
T_STA_SCHED_DRR = 1
T_STA_SCHED_ADRR = 1
T_STA_SCHED_TYPES = [T_STA_SCHED_RR, T_STA_SCHED_DRR, T_STA_SCHED_ADRR]

T_UE_SCHED_RR = 0
T_UE_SCHED_TYPES = [T_UE_SCHED_RR]


class WiFiSlicesDictField(fields.DictField):
    """A field that stores a regular Python dictionary."""

    def to_mongo(self, value):

        try:

            return serialize.serialize(value)

        except ValueError as ex:
            raise ValidationError(ex)

    def to_python(self, value):

        try:

            out = {}

            for slc in value.values():

                if not isinstance(slc, WiFiSlice):
                    slc = WiFiSlice(**slc)

                out[str(slc.slice_id)] = slc

            return out

        except ValueError as ex:
            raise ValidationError(ex)


class LTESlicesDictField(fields.DictField):
    """A field that stores a regular Python dictionary."""

    def to_mongo(self, value):

        try:

            return serialize.serialize(value)

        except ValueError as ex:
            raise ValidationError(ex)

    def to_python(self, value):

        try:

            out = {}

            for slc in value.values():

                if not isinstance(slc, LTESlice):
                    slc = LTESlice(**slc)

                out[str(slc.slice_id)] = slc

            return out

        except ValueError as ex:
            raise ValidationError(ex)


class EmbeddedWiFiProps(EmbeddedMongoModel):
    """Embedded Wi-Fi Properties."""

    ssid = SSIDField(required=True)

    bssid_type = fields.CharField(required=False,
                                  choices=T_BSSID_TYPE_TYPES,
                                  default=T_BSSID_TYPE_UNIQUE)

    allowed = fields.ListField(EtherAddressField())

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Poll """

        output = {}

        output['ssid'] = self.ssid
        output['bssid_type'] = self.bssid_type
        output['allowed'] = self.allowed

        return output


class EmbeddedLTEProps(EmbeddedMongoModel):
    """Embedded LTE Properties."""

    plmnid = PLMNIDField(required=True)

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the Poll """

        output = {}

        output['plmnid'] = self.plmnid

        return output


class Project(Env):
    """Project class.

    Attributes:
        owner: The username of the user that requested this pool
        wifi_props: The Wi-Fi properties
        lte_props: The LTE properties
        wifi_slices: The definition of the Wi-Fi slices
        lte_slices: The definition of the Wi-Fi slices

    The Wi-Fi properties are defined starting from a JSON document like the
    following:

    {
        "ssid": "EmPOWER",
        "allowed": ["11:22:33:44:55:66", "aa:bb:cc:dd:ee:ff"],
        "bssid_type": "unique"
    }

    The LTE properties are defined starting from a JSON document like the
    following:
    {
        "plmn_id": "222f93"
    }

    A Wi-Fi slice is defined starting from a JSON document like the
    following:

    {
        "slice_id": "0x42",
        "properties": {
            "amsdu_aggregation": true,
            "quantum": 12000,
            "sta_scheduler": 1
        }
    }

    The descriptor above will create a slice with id 0x42 on every WTP.

    In some cases it may be required to use different slice parameters only on
    certain WTPs. This can be done using a descriptor like the following:

    {
        "slice_id": "0x42",
        "properties": {
            "amsdu_aggregation": true,
            "quantum": 12000,
            "sta_scheduler": 1
        }
        "devices": {
            "00:0D:B9:2F:56:64": {
                "quantum": 15000
            }
        }
    }

    In this case the slice is still created on all the WTPs in the network,
    but some slice parameters are different for the specified nodes.

    Similarly, an LTE slice is defined starting from a JSON document like the
    following:

    {
        "slice_id": "0x42",
        "properties": {
            "rbgs": 5,
            "ue_scheduler": 1
        },
        "devices": {
            "aa:bb:cc:dd:ee:ff": {
                rbgs": 2
            }
        }
    }
    """

    owner = fields.CharField(required=True)
    desc = fields.CharField(required=True)
    wifi_props = fields.EmbeddedDocumentField(EmbeddedWiFiProps)
    lte_props = fields.EmbeddedDocumentField(EmbeddedLTEProps)
    wifi_slices = WiFiSlicesDictField(required=False, blank=True)
    lte_slices = LTESlicesDictField(required=False, blank=True)

    def upsert_wifi_slice(self, **kwargs):
        """Upsert new slice."""

        slc = WiFiSlice(**kwargs)

        for wtp in self.lvapp_manager.devices.values():
            for block in wtp.blocks.values():
                wtp.connection.send_set_slice(self, slc, block)

        self.wifi_slices[str(slc.slice_id)] = slc

        self.save()
        self.refresh_from_db()

        return slc.slice_id

    def upsert_lte_slice(self, **kwargs):
        """Upsert new slice."""

        slc = LTESlice(**kwargs)

        for vbs in self.vbsp_manager.devices.values():
            for cell in vbs.cells.values():
                vbs.connection.send_set_slice(self, slc, cell)

        self.lte_slices[str(slc.slice_id)] = slc

        self.save()
        self.refresh_from_db()

        return slc.slice_id

    def delete_wifi_slice(self, slice_id):
        """Delete slice."""

        if slice_id == "0":
            raise ValueError("Slice 0 cannot be deleted")

        slc = self.wifi_slices[slice_id]

        for wtp in self.lvapp_manager.devices.values():
            for block in wtp.blocks.values():
                wtp.connection.send_del_slice(self, slc.slice_id, block)

        del self.wifi_slices[slice_id]

        self.save()
        self.refresh_from_db()

    def delete_lte_slice(self, slice_id):
        """Delete slice."""

        if slice_id == "0":
            raise ValueError("Slice 0 cannot be deleted")

        slc = self.lte_slices[slice_id]

        for vbs in self.vbsp_manager.devices.values():
            for cell in vbs.cells.values():
                vbs.connection.send_del_slice(self, slc.slice_id, cell)

        del self.lte_slices[slice_id]

        self.save()
        self.refresh_from_db()

    @property
    def vbses(self):
        """Return the VBSes."""

        return self.vbsp_manager.devices

    @property
    def ueqs(self):
        """Return the UEs."""

        if not self.lte_props:
            return {}

        ueqs = {k: v for k, v in self.vbsp_manager.ueqs.items()
                if v.plmnid == self.lte_props.plmnid}

        return ueqs

    @property
    def wtps(self):
        """Return the WTPs."""

        return self.lvapp_manager.devices

    @property
    def lvaps(self):
        """Return the LVAPs."""

        if not self.wifi_props:
            return {}

        lvaps = {k: v for k, v in self.lvapp_manager.lvaps.items()
                 if v.ssid == self.wifi_props.ssid}

        return lvaps

    @property
    def vaps(self):
        """Return the VAPs."""

        if not self.wifi_props:
            return {}

        vaps = {k: v for k, v in self.lvapp_manager.vaps.items()
                if v.ssid == self.wifi_props.ssid}

        return vaps

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = super().to_dict()

        output['owner'] = self.owner

        output['desc'] = self.desc

        output['wifi_props'] = \
            self.wifi_props.to_dict() if self.wifi_props else None

        output['lte_props'] = \
            self.lte_props.to_dict() if self.lte_props else None

        output['wifi_slices'] = \
            self.wifi_slices if self.wifi_slices else None

        output['lte_slices'] = \
            self.lte_slices if self.lte_slices else None

        return output

    def get_prefix(self):
        """Return tenant prefix."""

        tokens = [self.project_id.hex[0:12][i:i + 2] for i in range(0, 12, 2)]
        return EtherAddress(':'.join(tokens))

    def generate_bssid(self, mac):
        """ Generate a new BSSID address. """

        base_mac = self.get_prefix()

        base = str(base_mac).split(":")[0:3]
        unicast_addr_mask = int(base[0], 16) & 0xFE
        base[0] = str(format(unicast_addr_mask, 'X'))
        suffix = str(mac).split(":")[3:6]

        return EtherAddress(":".join(base + suffix))
