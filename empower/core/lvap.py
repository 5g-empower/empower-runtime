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

"""EmPOWER Light Virtual Access Point (LVAP) class."""

import time

from empower.core.resourcepool import ResourceBlock
from empower.core.resourcepool import BANDS
from empower.core.resourcepool import BT_HT20
from empower.core.tenant import T_TYPE_SHARED
from empower.datatypes.etheraddress import EtherAddress
from empower.datatypes.ssid import SSID

import empower.logger

# add lvap message sent, status not received
PROCESS_SPAWNING = "spawning"

# add lvap message sent, status received
PROCESS_RUNNING = "running"

# del lvap message(s) sent, no status(es) received
PROCESS_REMOVING = "removing"


class LVAP:
    """ The EmPOWER Light Virtual Access Point

    One LVAP is created for every station probing the network (unless the MAC
    was blocked or if the MAC was not in the allowed list). An LVAP can be
    hosted by multiple WTPs. More preciselly an LVAP can be scheduled on one,
    and only one resource block in the downlink direction and on multiple
    resource blocks in the uplink direction. The downlink resource block is
    automatically also the default uplink resource block. The default uplink
    resource block is the resource block in charge of generating WiFi acks.
    Additional uplink resource blocks do not generate acks but can
    opportunistically receive and forward traffic. An unbound LVAP, i.e. an
    LVAP not hosted by any WTP, is not admissible.

    Handover can be performed by setting the wtp property of an lvap object to
    another wtp, e.g.:

      lvap.wtp = new_wtp

    where lvap is an instance of LVAP object and new_wtp is an instance of wtp
    object. The controller takes care of removing the lvap from the old wtp and
    spawing a new lvap on the target wtp. Stats are cleared on handovers. The
    new_wtp must support the same channel and band of the old wtp otherwise no
    handover is performed.

    An handover can also be perfomed by assigning a valid list of
    ResourceBlocks to the blocks property of an LVAP object. The first block in
    the list will be the downlink block while the other (if any) will be uplink
    blocks:

      lvap.blocks = blocks

    Notice how the blocks variable must be either a non empty list of
    ResourceBlocks or it must be a single ResourceBlock.

    The TX Policy configuration of the downlink resource block can be changed
    in the following way:

      lvap.txp.mcs = [1,2,3,4,5,6,7]

    Attributes:
        addr: The client's MAC Address as an EtherAddress instance.
        bssid: The currently active BSSID
        ssid: The currently active SSID
        authentication_state: set to True if the LVAP has already completed
          the open authentication handshake .
        association_state: set to True if the LVAP has already completed
          the association handshake.
        networks: The list of networks available for this LVAP.
        encap: encapsulate data traffic into an ethernet frame with the
          specified destationation address.
        assoc_id: association id for this LVAP (this cannot change
          after the LVAP has been spawned
        ssid: The currently associated SSID.
        tenant: the tenant to which this LVAP is associated (can be None).
        supported_band: the resource block advertised by the LVAP during the
          attachment procedure
        downlink: the single downlink/uplink block.
        uplink: zero or more uplink only blocks
    """

    def __init__(self, addr, assoc_id, state=None):

        # read only params
        self.addr = addr

        # the following parameters can be modified by both controller and
        # agent. the controller modified them with add_lvap messages (which
        # are then acked) the agent notifies the changes using status reports
        self._ssid = None
        self._bssid = None
        self.authentication_state = False
        self.association_state = False

        # list of networks available for this LVAP on the default block (0)
        self._networks = list()

        # if specified then send out wifi frames encapsulated into the
        # specified address, the field can only be modified by the controller
        self._encap = None

        # association id, this is generated once when the lvap is create and
        # then it is never changed
        self._assoc_id = assoc_id

        # supported band, this can be changed only by the controller as a
        # result of an add_lvap message, cannot be modified by the status
        # lvap message
        self._supported_band = None

        # current blocks (i.e. the interfaces on which the lvap is running)
        self._downlink = None
        self._uplink = []

        # the lvap state
        self._state = state

        # source blocks to be used for handover event
        self.source_blocks = None

        # target blocks to be used for handover
        self.target_blocks = None

        # migration sats
        self._timer = None

        # pending module ids (transions happen when list is empty)
        self.pending = []

        # logger :)
        self.log = empower.logger.get_logger()

    def handle_del_lvap_response(self, xid, _):
        """Received as result of a del lvap command."""

        if xid not in self.pending:
            self.log.error("Xid %u not in pending list, ignoring", xid)
            return

        if self.state not in [PROCESS_REMOVING]:
            self.log.error("Del lvap response received in state %s, ignoring",
                           self.state)
            return

        self.pending.remove(xid)

        # there are still pending transactions
        if self.pending:
            return

        # all blocks added, transition to spawning state
        if self.target_blocks:
            self.state = PROCESS_SPAWNING
            return

        self.log.error("Del lvap response received without target blocks")

    def handle_add_lvap_response(self, xid, _):
        """Received as result of a add lvap command."""

        if xid not in self.pending:
            self.log.error("Xid %u not in pending list, ignoring", xid)
            return

        if self.state not in [PROCESS_SPAWNING, PROCESS_RUNNING]:
            self.log.error("Add lvap response received in state %s, ignoring",
                           self.state)
            return

        self.pending.remove(xid)

        # there are still pending transactions
        if self.pending:
            return

        # all blocks add, transition to running state
        self.state = PROCESS_RUNNING

        # this add was the result of a handover, trigger event
        if self.state == PROCESS_RUNNING \
                and self.source_blocks \
                and self.source_blocks[0] is not None:

            self.blocks[0].radio.connection.server.\
                send_lvap_handover_message_to_self(self, self.source_blocks)

            self.source_blocks = None

    @property
    def state(self):
        """Return the state."""

        return self._state

    @state.setter
    def state(self, state):
        """Set the CPP."""

        self.log.info("LVAP %s transition %s->%s", self.addr, self.state,
                      state)

        if self.state:
            method = "_%s_%s" % (self.state, state)
        else:
            method = "_none_%s" % state

        if hasattr(self, method):
            callback = getattr(self, method)
            callback()
            return

        raise IOError("Invalid transistion %s -> %s" % (self.state, state))

    def _none_spawning(self):

        # set timer
        self._timer = time.time()

        # set new state
        self._state = PROCESS_SPAWNING

        # Set downlink block if different.
        self.__assign_downlink(self.target_blocks[0])

        # set uplink blocks
        self.__assign_uplink(self.target_blocks[1:])

    def _removing_spawning(self):

        # set new state
        self._state = PROCESS_SPAWNING

        # Set downlink block if different.
        self.__assign_downlink(self.target_blocks[0])

        # set uplink blocks
        self.__assign_uplink(self.target_blocks[1:])

        # reset target blocks
        self.target_blocks = None

    def _spawning_running(self):

        # set new state
        self._state = PROCESS_RUNNING

        # compute stats
        delta = int((time.time() - self._timer) * 1000)
        self._timer = None
        self.log.info("LVAP %s spawning took %sms", self.addr, delta)

        # send a probe response
        if self.tenant:
            wtp = self.blocks[0].radio
            wtp.connection.send_probe_response(self, self.tenant.tenant_name)

    def _running_removing(self):

        # set timer
        self._timer = time.time()

        # set new state
        self._state = PROCESS_REMOVING

        # send del lvap message
        wtp = self.blocks[0].radio
        if self.blocks[0].channel != self.target_blocks[0].channel:
            csa_switch_channel = self.target_blocks[0].channel
            xid = wtp.connection.send_del_lvap(self.addr, csa_switch_channel)
            self.pending.append(xid)
        else:
            xid = wtp.connection.send_del_lvap(self.addr)
            self.pending.append(xid)

        for block in self.blocks[1:]:
            xid = block.radio.connection.send_del_lvap(self.addr)
            self.pending.append(xid)

        # reset uplink and downlink
        self._downlink = None
        self._uplink = []

    def _running_running(self):

        pass

    def commit(self):
        """Send add lvap message for downlink and uplinks blocks."""

        if not self.blocks:
            return

        self.blocks[0].radio.connection.send_add_lvap(self,
                                                      self.blocks[0],
                                                      True)

        for block in self.blocks[1:]:
            block.radio.connection.send_add_lvap(self, block, False)

    @property
    def bssid(self):
        """Get the bssid."""

        return self._bssid

    @bssid.setter
    def bssid(self, bssid):
        """ Set the bssid. """

        if bssid == EtherAddress("00:00:00:00:00:00"):
            self._bssid = None
        else:
            self._bssid = bssid

    @property
    def ssid(self):
        """Get the ssid."""

        return self._ssid

    @ssid.setter
    def ssid(self, ssid):
        """ Set the ssid. """

        if ssid == SSID(b'\0'):
            self._ssid = None
        else:
            self._ssid = ssid

    @property
    def encap(self):
        """Get the encap."""

        return self._encap

    @encap.setter
    def encap(self, encap):
        """ Set the encap. """

        self._encap = encap

    @property
    def tenant(self):
        """Get the tenant."""

        from empower.main import RUNTIME

        return RUNTIME.load_tenant(self.ssid)

    @property
    def assoc_id(self):
        """Get the assoc_id."""

        return self._assoc_id

    @property
    def supported_band(self):
        """Get the supported_band."""

        return self._supported_band

    @supported_band.setter
    def supported_band(self, supported_band):
        """Set the assoc id."""

        self._supported_band = supported_band

    @property
    def networks(self):
        """Get the networks assigned to this LVAP."""

        return self._networks

    @networks.setter
    def networks(self, networks):
        """Set the ssids assigned to this LVAP."""

        self._networks = networks

    @property
    def txp(self):
        """ Get downlink transmission policy. """

        if not self.blocks:
            return None

        return self.blocks[0].tx_policies[self.addr]

    @property
    def blocks(self):
        """ Get the resource blocks assigned to this LVAP in the uplink. """

        return [self._downlink] + self._uplink

    @blocks.setter
    def blocks(self, blocks):
        """Assign a list of block to the LVAP.

        Assign a list of blocks to the LVAP. Accepts as input either a list or
        a ResourceBlock. If the list has more than one ResourceBlocks, then the
        first one is assigned to the downlink and the remaining are assigned
        to the uplink.

        Args:
            blocks: A list of ResourceBlocks or a ResourceBlock
        """

        if self.pending:
            raise ValueError("Handover in progress")

        if not blocks:
            return

        if isinstance(blocks, list):
            pool = blocks
        elif isinstance(blocks, ResourceBlock):
            pool = []
            pool.append(blocks)
        else:
            raise TypeError("Invalid type: %s" % type(blocks))

        for block in pool:
            if not isinstance(block, ResourceBlock):
                raise TypeError("Invalid type: %s" % type(block))

        # If LVAP is associated to a shared tenant, then reset LVAP
        if self.tenant and self.tenant.bssid_type == T_TYPE_SHARED:

            # check if tenant is available at target block
            bssid = self.tenant.generate_bssid(pool[0].hwaddr)

            # if not ignore request
            if bssid not in self.tenant.vaps:
                return

            # otherwise reset lvap
            self._ssid = None
            self.association_state = False
            self.authentication_state = False

        # save source blocks
        self.source_blocks = self.blocks

        # save target blocks
        self.target_blocks = pool

        if self.state is None:
            self.state = PROCESS_SPAWNING
        elif self.state == PROCESS_RUNNING:
            self.state = PROCESS_REMOVING
        else:
            IOError("Setting blocks on invalid state: %s" % self.state)

    def __assign_downlink(self, dl_block):
        """Set the downlink block."""

        # assign default transmission policy to the downlink resource block
        txp = dl_block.tx_policies[self.addr]

        if dl_block.channel > 14:
            txp.set_mcs([6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48.0, 54.0])
        else:
            txp.set_mcs([1.0, 2.0, 5.5, 11.0,
                         6.0, 9.0, 12.0, 18.0, 24.0, 36.0, 48.0, 54.0])

        if self.supported_band == BT_HT20:
            txp.set_ht_mcs([0, 1, 2, 3, 4, 5, 6, 7,
                            8, 9, 10, 11, 12, 13, 14, 15])
        else:
            txp.set_ht_mcs = ([])

        dl_block.radio.connection.send_set_transmission_policy(txp)

        # send add_lvap message
        dl_block.radio.connection.send_add_lvap(self, dl_block, True)

        # save block
        self._downlink = dl_block

    def __assign_uplink(self, ul_blocks):
        """Set the downlink blocks."""

        for block in ul_blocks:

            # send add_lvap message
            block.radio.connection.send_add_lvap(self, block, False)

            # save block into the list
            self._uplink.append(block)

    @property
    def wtp(self):
        """Return the wtp on which this LVAP is scheduled on."""

        if self.blocks[0]:
            return self.blocks[0].radio

        return None

    @wtp.setter
    def wtp(self, wtp):
        """Assigns LVAP to new wtp."""

        blocks = wtp.blocks() \
                    .filter_by_channel(self.blocks[0].channel) \
                    .filter_by_band(self.blocks[0].band) \
                    .first()

        self.blocks = blocks

    def clear_blocks(self):
        """Clear all blocks."""

        for block in self.blocks:
            block.radio.connection.send_del_lvap(self.addr)

        self._downlink = None
        self._uplink = []

    def to_dict(self):
        """ Return a JSON-serializable dictionary representing the LVAP """

        return {'addr': self.addr,
                'bssid': self.bssid,
                'ssid': self.ssid,
                'wtp': self.wtp,
                'blocks': self.blocks,
                'state': self.state,
                'supported_band': BANDS[self.supported_band],
                'assoc_id': self.assoc_id,
                'pending': self.pending,
                'encap': self.encap,
                'networks': self.networks,
                'authentication_state': self.authentication_state,
                'association_state': self.association_state}

    def __str__(self):

        accum = []
        accum.append("addr ")
        accum.append(str(self.addr))
        accum.append(" bssid ")
        accum.append(str(self.bssid))
        accum.append(" ssid ")
        accum.append(str(self.ssid))

        if self.networks:

            accum.append(" networks [ ")
            accum.append(str(self.networks[0]))

            for network in self.networks[1:]:
                accum.append(", ")
                accum.append(str(network))

            accum.append(" ]")

        accum.append(" assoc_id ")
        accum.append(str(self.assoc_id))

        if self.association_state:
            accum.append(" ASSOC")

        if self.authentication_state:
            accum.append(" AUTH")

        return ''.join(accum)

    def __hash__(self):
        return hash(self.addr)

    def __eq__(self, other):
        if isinstance(other, LVAP):
            return self.addr == other.addr
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
