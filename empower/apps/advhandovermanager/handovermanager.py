#!/usr/bin/env python3
#
# Copyright (c) 2018 Roberto Riggio
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

"""Basic LTE handover manager."""

from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class HandoverManager(EmpowerApp):
    """LTE Handover Manager application

    Command Line Parameters:

        tenant_id: tenant id
        every: loop period in ms (optional, default 5000ms)

    Example:

        ./empower-runtime.py apps.handovermanager.handovermanager \
            --tenant_id=8f83e794-1d07-4430-b5bd-db45d670c8f0
    """

    def __init__(self, **kwargs):

        # Flag to enable or disable load balacing algorithm
        self.__load_balance = True
        # Source cell downlink utilization threshold in percentage
        self.__s_dl_thr = 10
        # Source cell uplink utilization threshold in percentage
        self.__s_ul_thr = 10
        # Target cell downlink utilization threshold in percentage
        self.__t_dl_thr = 30
        # Target cell downlink utilization threshold in percentage
        self.__t_ul_thr = 30
        # RSRQ threshold to be handed over to a cell
        self.__rsrq_thr = -20
        # Maximum number of handovers that can performed from a cell at
        # each evaluation period
        self.__max_ho_from = 1
        # Maximum number of handovers that can performed to a cell at
        # each evaluation period
        self.__max_ho_to = 1

        EmpowerApp.__init__(self, **kwargs)

        self.vbsup(callback=self.vbs_up_callback)
        self.uejoin(callback=self.ue_join_callback)

    def vbs_up_callback(self, vbs):
        """ New VBS. """

        for cell in vbs.cells:

            report = self.cell_measurements(cell=cell,
                                            interval=self.every,
                                            callback=self.cell_measurements_callback)

    def cell_measurements_callback(self, report):
        """ New measurements available. """

        self.log.info("New cell measurements received from %s" % report.cell)

    def ue_join_callback(self, ue):
        """ New UE. """

        rrc_measurements_param = \
            [{"earfcn": ue.cell.DL_earfcn,
              "interval": 2000,
              "max_cells": 2,
              "max_measure": 2}]

        self.ue_measurements(ue=ue,
                             rrc_measurements_param=rrc_measurements_param,
                             callback=self.ue_measurements_callback)

    def ue_measurements_callback(self, ue):
        """ New measurements available. """

        self.log.info("New ue measurements received from %s" % ue.ue.ue_id)

    @property
    def load_balance(self):
        """Return flag to enable or disable load balacing algorithm."""

        return self.__load_balance

    @load_balance.setter
    def load_balance(self, value):
        """Set flag to enable or disable load balacing algorithm."""

        self.__load_balance = bool(value)

    @property
    def s_dl_thr(self):
        """Return source cell downlink utilization threshold."""

        return self.__s_dl_thr

    @s_dl_thr.setter
    def s_dl_thr(self, value):
        """Set source cell downlink utilization threshold."""

        thr = float(value)

        if thr < 0 or thr > 100:
            raise ValueError("Invalid value for s_dl_thr")

        self.__s_dl_thr = thr

    @property
    def s_ul_thr(self):
        """Return source cell uplink utilization threshold."""

        return self.__s_ul_thr

    @s_ul_thr.setter
    def s_ul_thr(self, value):
        """Set source cell uplink utilization threshold."""

        thr = float(value)

        if thr < 0 or thr > 100:
            raise ValueError("Invalid value for s_ul_thr")

        self.__s_ul_thr = thr

    @property
    def t_dl_thr(self):
        """Return target cell downlink utilization threshold."""

        return self.__t_dl_thr

    @t_dl_thr.setter
    def t_dl_thr(self, value):
        """Set target cell downlink utilization threshold."""

        thr = float(value)

        if thr < 0 or thr > 100:
            raise ValueError("Invalid value for v")

        self.__t_dl_thr = thr

    @property
    def t_ul_thr(self):
        """Return target cell uplink utilization threshold."""

        return self.__t_ul_thr

    @t_ul_thr.setter
    def t_ul_thr(self, value):
        """Set target cell uplink utilization threshold."""

        thr = float(value)

        if thr < 0 or thr > 100:
            raise ValueError("Invalid value for t_ul_thr")

        self.__t_ul_thr = thr

    @property
    def rsrq_thr(self):
        """Return RSRQ threshold to be handed over to a cell."""

        return self.__rsrq_thr

    @rsrq_thr.setter
    def rsrq_thr(self, value):
        """Set RSRQ threshold to be handed over to a cell."""

        thr = float(value)

        # RSRQ values ranges from -3 to -19.5
        if thr > -3 or thr < -20:
            raise ValueError("Invalid value for RSRQ threshold threshold")

        self.__rsrq_thr = thr

    @property
    def max_ho_from(self):
        """Return maximum number of handovers that can performed from a eNB at
        each evaluation period.
        """

        return self.__max_ho_from

    @max_ho_from.setter
    def max_ho_from(self, value):
        """Set maximum number of handovers that can performed from a eNB at
        each evaluation period.
        """

        self.__max_ho_from = int(value)

    @property
    def max_ho_to(self):
        """Return maximum number of handovers that can performed to a eNB at
        each evaluation period.
        """

        return self.__max_ho_to

    @max_ho_to.setter
    def max_ho_to(self, value):
        """Set maximum number of handovers that can performed to a eNB at
        each evaluation period.
        """

        self.__max_ho_to = int(value)

    def loop(self):
        """ Periodic job. """

        if not self.load_balance:
            return

        self.log.info("Running load balancing algorithm...")

        # Dictionary containing VBS which qualifies for performing handover
        ho_from_vbses = {}

        # Dictionary containing VBS which qualifies to receive handed over UEs
        ho_to_vbses = {}

        # Check the condition cellUtilDL > dl_thr or cellUtilUL > ul_thr.
        for vbs in self.vbses():

            if not vbs.is_online():
                continue

            for cell in vbs.cells:

                if not cell.cell_measurements:
                    continue

                self.log.info("Cell %s: DL: %f / %u / %u", cell,
                              cell.cell_measurements['mac_prbs_report'] \
                                ['DL_util_last'], self.s_dl_thr, self.t_dl_thr)

                self.log.info("Cell %s: UL: %f / %u / %u", cell,
                              cell.cell_measurements['mac_prbs_report'] \
                                ['UL_util_last'], self.s_ul_thr, self.t_ul_thr)

                if cell.cell_measurements['mac_prbs_report']['DL_util_last'] > \
                    self.s_dl_thr or \
                    cell.cell_measurements['mac_prbs_report']['UL_util_last'] > \
                    self.s_ul_thr:

                    if vbs.addr not in ho_from_vbses:
                        ho_from_vbses[vbs.addr] = {"vbs": vbs,
                                                   "cells": [],
                                                   "ues": self.ues(vbs),
                                                   "max_ho_from": 0}

                    ho_from_vbses[vbs.addr]["cells"].append(cell)

                if cell.cell_measurements['mac_prbs_report']['DL_util_last'] < \
                    self.t_dl_thr or \
                   cell.cell_measurements['mac_prbs_report']['UL_util_last'] < \
                    self.t_ul_thr:

                    if vbs.addr not in ho_to_vbses:
                        ho_to_vbses[vbs.addr] = {"vbs": vbs,
                                                 "cells": [],
                                                 "ues": self.ues(vbs),
                                                 "max_ho_to": 0}

                    ho_to_vbses[vbs.addr]["cells"].append(cell)

        # Find UEs and neighboring cells satisfying the handover conditions
        ho_info = {}

        for svbs in ho_from_vbses:

            # already too many hos from this vbs
            if ho_from_vbses[svbs]["max_ho_from"] >= self.max_ho_from:
                continue

            for ue in ho_from_vbses[svbs]["ues"]:

                for tvbs in ho_to_vbses:

                    # too many ho to this vbs
                    if ho_to_vbses[tvbs]["max_ho_to"] >= self.max_ho_to:
                        continue

                    # pick best cell in vbs
                    for cell in ho_to_vbses[tvbs]["cells"]:

                        # ignore current cell
                        if cell == ue.cell:
                            continue

                        # pick cell from measurements
                        if tvbs not in ue.ue_measurements:
                            continue
                        if cell not in ue.ue_measurements[tvbs]:
                            continue

                        current = ue.ue_measurements[ue.vbs.addr][ue.cell] \
                            ['rrc_measurements']["rsrq"]

                        new = ue.ue_measurements[tvbs][cell] \
                            ['rrc_measurements']["rsrq"]

                        if new > current and new > self.rsrq_thr:
                            ho_info[ue.ue_id] = {"ue": ue, "cell": cell}

                if ue.ue_id in ho_info and ho_info[ue.ue_id]:
                    tvbs = ho_info[ue.ue_id]['cell'].vbs.addr
                    ho_to_vbses[tvbs]["max_ho_to"] += 1
                    ho_from_vbses[svbs]["max_ho_from"] += 1

        # Handover the UEs
        for handover in ho_info.values():
            ue = handover['ue']
            cell = handover['cell']
            self.log.info("%s -> %s", ue, cell)
            ue.cell = cell


def launch(tenant_id,
           every=DEFAULT_PERIOD,
           load_balance=True,
           s_dl_thr=30,
           s_ul_thr=30,
           t_dl_thr=30,
           t_ul_thr=30,
           rsrq_thr=-20,
           max_ho_from=1,
           max_ho_to=1):
    """ Initialize the module. """

    return HandoverManager(tenant_id=tenant_id,
                           every=every,
                           load_balance=load_balance,
                           s_dl_thr=s_dl_thr,
                           s_ul_thr=s_ul_thr,
                           t_dl_thr=t_dl_thr,
                           t_ul_thr=t_ul_thr,
                           rsrq_thr=rsrq_thr,
                           max_ho_from=max_ho_from,
                           max_ho_to=max_ho_to)
