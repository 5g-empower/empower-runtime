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

from empower.main import RUNTIME

DEFAULT_SIGNALGRAPH_PERIOD = 2000

GRAPH_TOP_BOTTOM_MARGIN = 40
GRAPH_LEFT_RIGHT_MARGIN = 40
GRAPH_MAX_WIDTH = 550 - GRAPH_LEFT_RIGHT_MARGIN
GRAPH_MAX_HEIGHT = 750 - GRAPH_TOP_BOTTOM_MARGIN
MIN_DISTANCE = 70
N_XY = 300

UE_MAC_ADDR1 = 'A0:39:F7:4C:AA:0A'


class SignalGraph(EmpowerApp):
    """Signal strength visulization app.

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.signalgraph.signalgraph \
            --tenant_id=d18a6e8f-699b-4280-ab6f-435bd00e1c90
    """

    def __init__(self, **kwargs):

        EmpowerApp.__init__(self, **kwargs)
        self.graphData = {}

        self.vbses = []

        self.wtps = []
        self.wifi_data = {}

        self.coord = self.get_coordinates()

        self.vbsup(callback=self.vbs_up_callback)
        self.vbsdown(callback=self.vbs_down_callback)

        wtpup(tenant_id=self.tenant.tenant_id, callback=self.wtp_up_callback)

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

        for block in wtp.supports:

            ucqm(block=block,
                 tenant_id=self.tenant.tenant_id,
                 every=5000,
                 callback=self.ucqm_callback)

    def ucqm_callback(self, poller):
        """Called when a UCQM response is received from a WTP."""

        lvaps = RUNTIME.tenants[self.tenant.tenant_id].lvaps

        for addr in poller.maps.values():

            if addr['addr'].to_str() == UE_MAC_ADDR1:
                if addr['addr'] in lvaps and lvaps[addr['addr']].wtp:
                    active_flag = 1

                    if (lvaps[addr['addr']].wtp.addr != poller.block.addr):
                        active_flag = 0
                    elif ((lvaps[addr['addr']].wtp.addr == poller.block.addr  \
                        and (lvaps[addr['addr']].association_state == False))):
                        active_flag = 0

                    if poller.block.addr.to_str() not in self.wtps:
                        self.wtps.append(poller.block.addr.to_str())

                    self.wifi_data[poller.block.addr.to_str()] = \
                                {
                                    'rssi': addr['mov_rssi'],
                                    'wtp': poller.block.addr.to_str(),
                                    'active': active_flag
                                }
                elif addr['addr'] not in lvaps:
                    self.wifi_data = {}
                    break


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
        graph_nodes = []

        for wtp in self.wtps:
            # Append the WTP's info
            graph_nodes.append({
                                'id': node_id,
                                'node_id': wtp,
                                'entity': 'wtp',
                                'tooltip': 'MAC',
                                'x': self.coord[node_id][0],
                                'y': self.coord[node_id][1]
                              })
            node_id += 1

        for vbs in self.vbses:

            # List containing all the neighbor cells of all UEs
            neigh_cells = []

            serving_vbs = {
                            'id': node_id,
                            'node_id': vbs.enb_id,
                            'entity': 'enb',
                            'tooltip': 'eNB Id',
                            'x': self.coord[node_id][0],
                            'y': self.coord[node_id][1]
                          }

            graph_nodes.append(serving_vbs)

            for ue in vbs.ues:

                node_id += 1

                # Append the UE's info
                graph_nodes.append({
                                    'id': node_id,
                                    'node_id': vbs.ues[ue].rnti,
                                    'entity': 'ue',
                                    'tooltip': 'RNTI',
                                    'x': self.coord[node_id][0],
                                    'y': self.coord[node_id][1]
                                  })

                # Index of UE in nodes array
                ue_index = node_id

                # Neighbor cells list per UE
                cells = self.get_neigh_cells(vbs.ues[ue])

                for cell in cells:
                    if cell not in neigh_cells:
                        # Increment the node id
                        node_id += 1

                        graph_nodes.append({
                                            'id': node_id,
                                            'node_id': cell,
                                            'entity': 'enb',
                                            'tooltip': 'PCI',
                                            'x': self.coord[node_id][0],
                                            'y': self.coord[node_id][1]
                                            })

                        neigh_cells.append(cell)

                # Index of cell in nodes array
                cell_index = None

                # Store primary cell measurements per UE
                for n in graph_nodes:
                    if (n['node_id'] == vbs.enb_id) and (n['entity'] == 'enb'):
                        cell_index = n['id']
                        break

                graph_links.append({
                                    'src': cell_index,
                                    'dst': ue_index,
                                    'rsrp': vbs.ues[ue].pcell_rsrp,
                                    'rsrq': vbs.ues[ue].pcell_rsrq,
                                    'rssi': None,
                                    'entity': 'lte',
                                    'color': 'orange',
                                    'width': 6
                                    })

                measurements = vbs.ues[ue].rrc_meas

                for key, m in measurements.items():

                    cell_index = None

                    for n in graph_nodes:
                        if (n['node_id'] == key) and (n['entity'] == 'enb'):
                            cell_index = n['id']
                            break
                    # Add each link for a measured neighbor cell
                    graph_links.append({
                                            'src': cell_index,
                                            'dst': ue_index,
                                            'rsrp': m['rsrp'],
                                            'rsrq': m['rsrq'],
                                            'rssi': None,
                                            'entity': 'lte',
                                            'color': 'black',
                                            'width': 4
                                       })

                wtp_index = 0

                for k, v in self.wifi_data.items():

                    for n in graph_nodes:
                        if (n['node_id'] == v['wtp'])  \
                                                    and (n['entity'] == 'wtp'):
                            wtp_index = n['id']
                            break

                    color = 'black'
                    width = 4

                    if v['active'] == 1:
                        width = 6
                        color = 'lightgreen'

                    # Add each link for a measured WTP
                    graph_links.append({
                                        'src': wtp_index,
                                        'dst': ue_index,
                                        'rsrp': None,
                                        'rsrq': None,
                                        'rssi': v['rssi'],
                                        'entity': 'wifi',
                                        'color': color,
                                        'width': width
                                       })

        self.graphData = {
                            'nodes': graph_nodes,
                            'links': graph_links
                          }

def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return SignalGraph(tenant_id=tenant_id, every=DEFAULT_SIGNALGRAPH_PERIOD)
