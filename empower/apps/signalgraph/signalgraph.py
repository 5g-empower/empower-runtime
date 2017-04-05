#!/usr/bin/env python3
#
# Copyright (c) 2016 Supreeth Herle
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

"""Signal strength visulization app."""

import random

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.main import RUNTIME
from empower.maps.ucqm import ucqm
from empower.events.wtpup import wtpup
from empower.events.wtpdown import wtpdown
from empower.events.vbsup import vbsup
from empower.events.vbsdown import vbsdown

from empower.main import RUNTIME

DEFAULT_SIGNALGRAPH_PERIOD = 2000

GRAPH_TOP_BOTTOM_MARGIN = 40
GRAPH_LEFT_RIGHT_MARGIN = 40
GRAPH_MAX_WIDTH = 550 - GRAPH_LEFT_RIGHT_MARGIN
GRAPH_MAX_HEIGHT = 750 - GRAPH_TOP_BOTTOM_MARGIN
MIN_DISTANCE = 70
N_XY = 300


class SignalGraph(EmpowerApp):
    """Signal strength visulization app.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.signalgraph.signalgraph \
            --tenant_id=8f83e794-1d07-4430-b5bd-db45d670c8f0
    """

    def __init__(self, **kwargs):

        EmpowerApp.__init__(self, **kwargs)

        self.graphData = {}
        self.wifi_data = {}

        # List of VBSes active
        self.vbses = []
        # List of WTPs active
        self.wtps = []

        # Populate existing VBSes
        for vbs in self.tenant.vbses.values():
            if vbs.connection:
                self.vbses.append(vbs)

        # Populate existing WTPs and trigger UCQM for existing WTPs
        for wtp in self.tenant.wtps.values():
            if wtp.connection:
                self.wtps.append(wtp)

                for block in wtp.supports:
                    ucqm(block=block,
                         tenant_id=self.tenant.tenant_id,
                         every=5000,
                         callback=self.ucqm_callback)

        # Generating inital coordinates for the graph nodes
        self.coord = self.get_coordinates()

        vbsup(tenant_id=self.tenant.tenant_id, callback=self.vbs_up_callback)
        vbsdown(tenant_id=self.tenant.tenant_id, callback=self.vbs_down_callback)

        wtpup(tenant_id=self.tenant.tenant_id, callback=self.wtp_up_callback)
        wtpdown(tenant_id=self.tenant.tenant_id, callback=self.wtp_up_callback)

    def get_coordinates(self):

        rangeX = (GRAPH_LEFT_RIGHT_MARGIN, GRAPH_MAX_WIDTH)
        rangeY = (GRAPH_TOP_BOTTOM_MARGIN, GRAPH_MAX_HEIGHT)

        deltas = set()
        for x in range(-MIN_DISTANCE, MIN_DISTANCE + 1):
            for y in range(-MIN_DISTANCE, MIN_DISTANCE + 1):
                if (x * x) + (y * y) >= MIN_DISTANCE * MIN_DISTANCE:
                    deltas.add((x,y))

        randPoints = []
        excluded = set()
        count = 0
        while count < N_XY:
            x = random.randrange(*rangeX)
            y = random.randrange(*rangeY)

            if (x, y) in excluded:
                continue

            randPoints.append((x, y))
            count += 1

            excluded.update((x + dx, y + dy) for (dx, dy) in deltas)

        return randPoints

    def to_dict(self):
        """Return json-serializable representation of the object."""

        out = super().to_dict()
        out['graphData'] = self.graphData

        return out

    def vbs_up_callback(self, vbs):
        """Called when an VBS connects to a tenant."""

        # Append VBS to list of active VBSs
        if vbs not in self.vbses:
            self.vbses.append(vbs)

    def vbs_down_callback(self, vbs):
        """Called when an VBS disconnects from a tenant."""

        # Removes VBS from list of active VBSs
        if vbs in self.vbses:
            self.vbses.remove(vbs)

    def wtp_up_callback(self, wtp):
        """Called when a new WTP connects to the controller."""

        if wtp not in self.wtps:
            self.wtps.append(wtp)

        for block in wtp.supports:

            ucqm(block=block,
                 tenant_id=self.tenant.tenant_id,
                 every=5000,
                 callback=self.ucqm_callback)

    def wtp_down_callback(self, wtp):
        """Called when a WTP disconnects from the controller."""

        # Cleanup ucqm module instance associated with this WTP.

        # Removes WTP from list of active WTPs
        if wtp in self.wtps:
            self.wtps.remove(wtp)

    def ucqm_callback(self, poller):
        """Called when a UCQM response is received from a WTP."""

        lvaps = RUNTIME.tenants[self.tenant.tenant_id].lvaps

        for addr in poller.maps.values():

            if addr['addr'] in lvaps and lvaps[addr['addr']].wtp:
                active_flag = 1

                if (lvaps[addr['addr']].wtp.addr != poller.block.addr):
                    active_flag = 0
                elif ((lvaps[addr['addr']].wtp.addr == poller.block.addr  \
                    and (lvaps[addr['addr']].association_state == False))):
                    active_flag = 0

                self.wifi_data[poller.block.addr.to_str() + addr['addr'].to_str()] = \
                                    {
                                        'rssi': addr['mov_rssi'],
                                        'wtp': poller.block.addr.to_str(),
                                        'sta': addr['addr'].to_str(),
                                        'active': active_flag
                                    }

            elif poller.block.addr.to_str() + addr['addr'].to_str() in self.wifi_data:
                del self.wifi_data[poller.block.addr.to_str() + addr['addr'].to_str()]

    def get_neigh_cells(self, ue):
        """Fetches list of neighbor cells as seen by UE."""

        measurements = ue.rrc_meas

        neigh_cells = []

        for m in measurements.keys():
            # Append the Physical Cell ID of neighboring cells
            neigh_cells.append(m)

        return neigh_cells

    def loop(self):
        """ Periodic job. """

        node_id = 0
        # Contains all links between cells and UEs
        graph_links = []
        # Contains all nodes in the graph
        graph_nodes = {}
        # Contains existing LTE UEs mac addresses
        ue_mac = []

        tenant = RUNTIME.tenants[self.tenant.tenant_id]

        for wtp in self.wtps:
            # Append the WTP's info
            graph_nodes['wtp' + wtp.addr.to_str()] =  \
                                            {
                                                'id': node_id,
                                                'node_id': wtp.addr.to_str(),
                                                'entity': 'wtp',
                                                'tooltip': 'MAC',
                                                'x': self.coord[node_id][0],
                                                'y': self.coord[node_id][1]
                                            }
            node_id += 1

        for vbs in self.vbses:

            graph_nodes['enb' + vbs.addr.to_str()] = \
                                                {
                                                    'id': node_id,
                                                    'node_id': vbs.enb_id,
                                                    'entity': 'enb',
                                                    'tooltip': 'eNB Id',
                                                    'x': self.coord[node_id][0],
                                                    'y': self.coord[node_id][1]
                                                }
            node_id += 1

        for ue in tenant.ues.values():

            mac = None

            if ue.imsi and ue.imsi in RUNTIME.imsi2mac:
                mac = RUNTIME.imsi2mac[ue.imsi].to_str()

            # Append the UE's info
            graph_nodes['ue' + ue.vbs.addr.to_str() + str(ue.rnti)] = \
                                            {
                                                'id': node_id,
                                                'node_id': ue.rnti,
                                                'vbs_id': ue.vbs.enb_id,
                                                'mac': mac,
                                                'entity': 'ue',
                                                'tooltip': 'RNTI (MAC)',
                                                'x': self.coord[node_id][0],
                                                'y': self.coord[node_id][1]
                                            }

            # Index of UE in nodes array
            ue_index = node_id

            # Link between UE and serving eNB (VBS)
            graph_links.append({
                                    'src': graph_nodes['enb' + ue.vbs.addr.to_str()]['id'],
                                    'dst': ue_index,
                                    'rsrp': ue.pcell_rsrp,
                                    'rsrq': ue.pcell_rsrq,
                                    'rssi': None,
                                    'entity': 'lte',
                                    'color': 'orange',
                                    'width': 6
                                })

            node_id += 1

            # Neighbor cells list per UE
            cells = self.get_neigh_cells(ue)

            for cell in cells:

                if 'enb' + str(cell) not in graph_nodes:

                    graph_nodes['enb' + str(cell)] = \
                                                {
                                                    'id': node_id,
                                                    'node_id': cell,
                                                    'entity': 'enb',
                                                    'tooltip': 'PCI',
                                                    'x': self.coord[node_id][0],
                                                    'y': self.coord[node_id][1]
                                                }

                     # Increment the node id
                    node_id += 1

            # Add each link for a measured neighbor cell
            measurements = ue.rrc_meas

            for key, m in measurements.items():

                graph_links.append({
                                        'src': graph_nodes['enb' + str(key)]['id'],
                                        'dst': ue_index,
                                        'rsrp': m['rsrp'],
                                        'rsrq': m['rsrq'],
                                        'rssi': None,
                                        'entity': 'lte',
                                        'color': 'black',
                                        'width': 4
                                   })

            if mac:

                ue_mac.append(mac)

                for k, v in self.wifi_data.items():
                    # Check for links pertaining to each LTE UE
                    if k.endswith(mac):

                        color = 'black'
                        width = 4

                        if v['active'] == 1:
                            width = 6
                            color = 'lightgreen'

                        # Add each link for a measured WTP
                        graph_links.append({
                                            'src': graph_nodes['wtp' + v['wtp']]['id'],
                                            'dst': ue_index,
                                            'rsrp': None,
                                            'rsrq': None,
                                            'rssi': v['rssi'],
                                            'entity': 'wifi',
                                            'color': color,
                                            'width': width
                                           })


        lvaps = RUNTIME.tenants[self.tenant.tenant_id].lvaps

        for sta in lvaps.values():
            # Check for preventing addition of LTE UEs as Wifi Stations
            if sta.addr.to_str() not in ue_mac:
                # Append the LVAP's info
                graph_nodes['sta' + sta.addr.to_str()] =  \
                                            {
                                                'id': node_id,
                                                'node_id': sta.addr.to_str(),
                                                'entity': 'sta',
                                                'tooltip': 'MAC',
                                                'x': self.coord[node_id][0],
                                                'y': self.coord[node_id][1]
                                            }

                for k, v in self.wifi_data.items():
                    # Check for links pertaining to each WIFI station
                    if k.endswith(sta.addr.to_str()):

                        color = 'black'
                        width = 4

                        if v['active'] == 1:
                            width = 6
                            color = 'lightgreen'

                        # Add each link for a measured WTP
                        graph_links.append({
                                            'src': graph_nodes['wtp' + v['wtp']]['id'],
                                            'dst': node_id,
                                            'rsrp': None,
                                            'rsrq': None,
                                            'rssi': v['rssi'],
                                            'entity': 'wifi',
                                            'color': color,
                                            'width': width
                                           })

                node_id += 1

        self.graphData = {
                            'nodes': graph_nodes.values(),
                            'links': graph_links
                          }

def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return SignalGraph(tenant_id=tenant_id, every=DEFAULT_SIGNALGRAPH_PERIOD)
