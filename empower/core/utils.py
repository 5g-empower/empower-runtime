#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio, Estefania Coronado
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

"""EmPOWER utils."""

import random

from empower.datatypes.etheraddress import EtherAddress


def ofmatch_d2s(key):
    """Convert an OFMatch from dictionary to string."""

    match = ",".join(["%s=%s" % x for x in sorted(key.items())])
    return match


def ofmatch_s2d(match):
    """Convert an OFMatch from string to dictionary."""

    key = {}

    if match == "":
        return key

    for token in match.split(","):
        key_t, value_t = token.split("=")

        if key_t == 'dl_vlan':
            value_t = int(value_t)

        if key_t == 'dl_type':
            value_t = int(value_t, 16)

        if key_t == 'in_port':
            value_t = int(value_t)

        if key_t == 'nw_proto':
            value_t = int(value_t, 16)

        if key_t == 'tp_dst':
            value_t = int(value_t)

        if key_t == 'tp_src':
            value_t = int(value_t)

        key[key_t] = value_t

    return key


def get_xid():
    """Return randon 32bits integers to be used as mod_id."""

    return random.getrandbits(32)


def hex_to_ether(in_hex):
    """Convert Int to EtherAddress."""

    str_hex_value = format(in_hex, 'x')
    padding = '0' * (12 - len(str_hex_value))
    mac_string = padding + str_hex_value
    mac_string_array = \
        [mac_string[i:i+2] for i in range(0, len(mac_string), 2)]

    return EtherAddress(":".join(mac_string_array))


def ether_to_hex(ether):
    """Convert EtherAddress to Int."""

    return int.from_bytes(ether.to_raw(), byteorder='big')


def generate_bssid(base_mac, sta_mac):
    """ Generate a new BSSID address. """

    base = str(base_mac).split(":")[0:3]
    unicast_addr_mask = int(base[0], 16) & 0xFE
    base[0] = str(format(unicast_addr_mask, 'X'))
    sta = str(sta_mac).split(":")[3:6]
    return EtherAddress(":".join(base + sta))
