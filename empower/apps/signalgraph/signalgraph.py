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

import numpy as np
from random import randrange as rd

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD
from empower.main import RUNTIME

DEFAULT_SIGNALGRAPH_PERIOD = 2000

GRAPH_TOP_BOTTOM_MARGIN = 30
GRAPH_LEFT_RIGHT_MARGIN = 30
GRAPH_MAX_WIDTH = 550 - GRAPH_LEFT_RIGHT_MARGIN
GRAPH_MAX_HEIGHT = 680 - GRAPH_TOP_BOTTOM_MARGIN

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
        self.vbses = []
        self.graphData = {}
        self.coord_x = np.random.uniform(
                                        low = GRAPH_LEFT_RIGHT_MARGIN,
                                        high = GRAPH_MAX_WIDTH,
                                        size = 500)
        self.coord_y = np.random.uniform(
                                        low = GRAPH_TOP_BOTTOM_MARGIN,
                                        high = GRAPH_MAX_HEIGHT,
                                        size = 500)

        self.vbsup(callback=self.vbs_up_callback)
        self.vbsdown(callback=self.vbs_down_callback)

    def to_dict(self):
        """Return json-serializable representation of the object."""

        out = super().to_dict()
        # out['graphData'] = self.graphData
        nodes = [{
                    'id': 0,
                    'node_id': 3617,
                    'entity': 'enb',
                    'tooltip': 'eNB Id',
                    'x': self.coord_x[0],
                    'y': self.coord_y[0]
                },
                {
                    'id': 1,
                    'node_id': 206,
                    'entity': 'enb',
                    'tooltip': 'PCI',
                    'x': self.coord_x[1],
                    'y': self.coord_y[1]
                },
                {
                    'id': 2,
                    'node_id': 198,
                    'entity': 'enb',
                    'tooltip': 'PCI',
                    'x': self.coord_x[2],
                    'y': self.coord_y[2]
                }
                ,{
                    'id': 3,
                    'node_id': 15,
                    'entity': 'enb',
                    'tooltip': 'PCI',
                    'x': self.coord_x[3],
                    'y': self.coord_y[3]
                },
                {
                    'id': 4,
                    'node_id': 56171,
                    'entity': 'ue',
                    'tooltip': 'RNTI',
                    'x': self.coord_x[4],
                    'y': self.coord_y[4]
                },
                {
                    'id': 5,
                    'node_id': 33456,
                    'entity': 'ue',
                    'tooltip': 'RNTI',
                    'x': self.coord_x[5],
                    'y': self.coord_y[5]
                },
                {
                    'id': 6,
                    'node_id': '00:00:00:00:0F:21',
                    'entity': 'wtp',
                    'tooltip': 'MAC',
                    'x': self.coord_x[6],
                    'y': self.coord_y[6]
                }]

        links = [{
                    'src': 0,
                    'dst': 4,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'orange',
                    'entity': 'lte',
                    'width': 6
                },
                {
                    'src': 0,
                    'dst': 5,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'orange',
                    'entity': 'lte',
                    'width': 6
                },
                {
                    'src': 1,
                    'dst': 4,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'black',
                    'entity': 'lte',
                    'width': 4
                },
                {
                    'src': 2,
                    'dst': 4,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'black',
                    'entity': 'lte',
                    'width': 4
                },
                {
                    'src': 3,
                    'dst': 4,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'black',
                    'entity': 'lte',
                    'width': 4
                },
                {
                    'src': 1,
                    'dst': 5,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'black',
                    'entity': 'lte',
                    'width': 4
                },
                {
                    'src': 2,
                    'dst': 5,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'black',
                    'entity': 'lte',
                    'width': 4
                },
                {
                    'src': 3,
                    'dst': 5,
                    'rsrp': rd(-140, -44, 1),
                    'rsrq': rd(-19, -3, 1),
                    'rssi': None,
                    'color': 'black',
                    'entity': 'lte',
                    'width': 4
                },
                {
                    'src': 6,
                    'dst': 4,
                    'rsrp': None,
                    'rsrq': None,
                    'rssi': rd(-100, -50, 1),
                    'color': 'lightgreen',
                    'entity': 'wifi',
                    'width': 6
                },
                {
                    'src': 6,
                    'dst': 5,
                    'rsrp': None,
                    'rsrq': None,
                    'rssi': rd(-100, -50, 1),
                    'color': 'lightgreen',
                    'entity': 'wifi',
                    'width': 6
                }]

        out['graphData'] = {}
        out['graphData']['00:00:00:00:0E:21'] = {
                                                'nodes': nodes,
                                                'links': links
                                                }
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

    def get_neigh_cells(self, ue):
        """Fetches list of neighbor cells as seen by UE."""

        measurements = ue.rrc_meas

        neigh_cells = []

        for m in measurements.keys():
            # Append the Physical Cell ID of neighboring cells
            neigh_cells.extend(m)

        return neigh_cells

    def loop(self):
        """ Periodic job. """

        for vbs in self.vbses:

            node_id = 0

            # List containing all the neighbor cells of all UEs
            neigh_cells = []
            # Contains all links between cells and UEs
            graph_links = []
            # Contains all nodes in the graph
            graph_nodes = []

            serving_vbs = {
                            'id': node_id,
                            'node_id': vbs.enb_id,
                            'entity': 'enb',
                            'tooltip': 'eNB Id',
                            'x': self.coord_x[node_id],
                            'y': self.coord_y[node_id]
                          }

            graph_nodes.append(serving_vbs)

            for ue in vbs.ues:

                node_id += 1

                # Append the UE's info
                graph_nodes.append({
                                    'id': node_id,
                                    'node_id': ue.rnti,
                                    'entity': 'ue',
                                    'tooltip': 'RNTI',
                                    'x': self.coord_x[node_id],
                                    'y': self.coord_y[node_id]
                                  })

                # Index of UE in nodes array
                ue_index = node_id

                # Neighbor cells list per UE
                cells = self.get_neigh_cells(ue)

                for cell in cells:
                    if cell not in neigh_cells:
                        # Increment the node id
                        node_id += 1

                        graph_nodes.append({
                                            'id': node_id,
                                            'node_id': cell,
                                            'entity': 'enb',
                                            'tooltip': 'PCI',
                                            'x': self.coord_x[node_id],
                                            'y': self.coord_y[node_id]
                                            })

                # Index of cell in nodes array
                cell_index = 0

                # Store primary cell measurements per UE
                for n in graph_nodes:
                    if (n.node_id == vbs.enb_id) and (n.entity == 'enb'):
                        cell_index = n.id
                        break

                graph_links.append({
                                    'src': cell_index,
                                    'dst': ue_index,
                                    'rsrp': ue.pcell_rsrp,
                                    'rsrq': ue.pcell_rsrq,
                                    'rssi': None,
                                    'entity': 'lte',
                                    'color': 'orange',
                                    'width': 6
                                    })

                measurements = ue.rrc_meas

                for key, m in measurements.items():

                    cell_index = 0

                    for n in graph_nodes:
                        if (n.node_id == key) and (n.entity == 'enb'):
                            cell_index = n.id
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

            self.graphData[vbs.addr] = {
                                            'nodes': graph_nodes,
                                            'links': graph_links
                                       }

def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return SignalGraph(tenant_id=tenant_id, every=DEFAULT_SIGNALGRAPH_PERIOD)
