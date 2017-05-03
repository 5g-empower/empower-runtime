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

"""VBS RRC Stats Module."""

from protobuf_to_dict import protobuf_to_dict
from empower.vbsp.messages import statistics_pb2
from empower.vbsp.messages import configs_pb2
from empower.vbsp.messages import main_pb2
from empower.core.ue import UE
from empower.datatypes.etheraddress import EtherAddress
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import ModuleTrigger
from empower.vbs_stats import RRC_STATS_RAT_TYPE
from empower.vbs_stats import RRC_STATS_REPORT_CONF_TYPE
from empower.vbs_stats import RRC_STATS_TRIGGER_QUANT
from empower.vbs_stats import RRC_STATS_BW
from empower.vbs_stats import RRC_STATS_REPORT_INTR
from empower.vbs_stats import RRC_STATS_NUM_REPORTS
from empower.vbs_stats import RRC_STATS_EVENT_THRESHOLD_TYPE
from empower.vbs_stats import PRT_VBSP_RRC_STATS
from empower.vbsp import PRT_UE_LEAVE
from empower.vbsp.vbspconnection import create_header
from empower.core.utils import ether_to_hex
from empower.core.app import EmpowerApp

from empower.main import RUNTIME


class VBSRRCStats(ModuleTrigger):
    """ VBSRRCStats object. """

    MODULE_NAME = "vbs_rrc_stats"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'ue', 'meas_req']

    def __init__(self):

        ModuleTrigger.__init__(self)

        # parameters
        self._ue = None
        self._meas_req = None

        # data structures
        self._meas_reply = None
        self._meas = {}

    @property
    def ue(self):
        """Return UE."""

        return self._ue

    @ue.setter
    def ue(self, value):
        """Set UE."""

        self._ue = value

    @property
    def meas_req(self):
        """Return configuration of RRC measurements requested."""

        return self._meas_req

    @meas_req.setter
    def meas_req(self, value):
        """Set configuration of RRC measurements requested."""

        if self.meas_req:
            raise ValueError("Cannot update configuration")

        if "rat_type" not in value:
            raise ValueError("Missing measurement RAT type")

        if value["rat_type"] not in RRC_STATS_RAT_TYPE:
            raise ValueError("Invalid measurement RAT type")

        if "bandwidth" not in value:
            raise ValueError("Missing measurement bandwidth (num. of RBs)")

        if value["bandwidth"] not in RRC_STATS_BW:
            raise ValueError("Invalid measurement bandwidth (num. of RBs)")

        if "carrier_freq" not in value:
            raise ValueError("Missing frequency (EARFCN) to measure parameter")

        if "cells_to_measure" in value and len(value["cells_to_measure"]) > 32:
            raise ValueError("Num. of cells to measure must be < 32")

        if "blacklist_cells" in value and len(value["blacklist_cells"]) > 32:
            raise ValueError("Num. of blacklist cells must be < 32")

        if "report_type" not in value:
            raise ValueError("Missing measurement report type")

        if value["report_type"] not in RRC_STATS_REPORT_CONF_TYPE:
            raise ValueError("Invalid measurement report type")

        if value["report_type"] == "A3" and "a3_offset" not in value:
            raise ValueError("Missing a3_offset parameter for A3 event")

        if value["report_type"] in ["A1", "A2", "A4", "A5"] and "threshold1" not in value:

            raise ValueError("Missing threshold1 parameter for given event")

        if value["report_type"] in ["A1", "A2", "A4", "A5"]:

            if "type" not in value["threshold1"]:
                raise ValueError("Missing threshold1 type parameter")

            if value["threshold1"]["type"] not in RRC_STATS_EVENT_THRESHOLD_TYPE:
                raise ValueError("Invalid threshold1 type parameter")

            if "value" not in value["threshold1"]:
                raise ValueError("Missing threshold1 value parameter")

        if value["report_type"] == "A5" and "threshold2" not in value:
            raise ValueError("Missing threshold2 parameter for A5 event")

        if value["report_type"] == "A5":

            if "type" not in value["threshold2"]:
                raise ValueError("Missing threshold2 type parameter")

            if value["threshold2"]["type"] not in RRC_STATS_EVENT_THRESHOLD_TYPE:
                raise ValueError("Invalid threshold2 type parameter")

            if "value" not in value["threshold2"]:
                raise ValueError("Missing threshold2 value parameter")

            if value["threshold2"]["type"] != value["threshold1"]["type"]:
                raise ValueError("threshold1 and threshold2 must be equal")

        if "report_interval" not in value:
            raise ValueError("Missing interval between reports parameter")

        if value["report_interval"] not in RRC_STATS_REPORT_INTR:
            raise ValueError("Interval b/w reports must be b/w 1 & 3600 secs")

        if "trigger_quantity" not in value:
            raise ValueError("Missing trigger_quantity parameter")

        if value["trigger_quantity"] not in RRC_STATS_TRIGGER_QUANT:
            raise ValueError("Invalid trigger_quantity parameter")

        if "num_of_reports" not in value:
            raise ValueError("Missing num_of_reports parameter")

        if value["num_of_reports"] not in RRC_STATS_NUM_REPORTS:
            raise ValueError("Invalid Num. of measurement reports to report")

        if "max_report_cells" not in value:
            raise ValueError("Missing max_report_cells parameter")

        if value["max_report_cells"] > 8 or value["max_report_cells"] < 1:
            raise ValueError("Max. cells to report must be b/w 1 & 8")

        self._meas_req = value

    @property
    def meas(self):
        """Return all the RRC measurements for this module."""

        return self._meas

    @property
    def meas_reply(self):
        """Return RRC measurements reply."""

        return self._meas_reply

    @meas_reply.setter
    def meas_reply(self, response):
        """Set RRC measurements reply."""

        tenant = RUNTIME.tenants[self.tenant_id]
        ue = tenant.ues[self.ue]

        self._meas_reply = protobuf_to_dict(response)
        event_type = response.WhichOneof("event_types")
        meas = self._meas_reply[event_type]["mRRC_meas"]["repl"]

        if "PCell_rsrp" in meas:
            ue.pcell_rsrp = meas["PCell_rsrp"]

        if "PCell_rsrq" in meas:
            ue.pcell_rsrq = meas["PCell_rsrq"]

        if "neigh_meas" in meas:

            for k in meas["neigh_meas"].keys():

                if k == "EUTRA_meas":

                    # EUTRA measurement result
                    for m in meas["neigh_meas"][k]:

                        if m["phys_cell_id"] not in ue.rrc_meas:
                            self._meas[m["phys_cell_id"]] = {}
                            ue.rrc_meas[m["phys_cell_id"]] = {}

                        ue.rrc_meas[m["phys_cell_id"]]["RAT_type"] = "EUTRA"

                        if "meas_result" in m:

                            if "rsrp" in m["meas_result"]:
                                self._meas[m["phys_cell_id"]]["rsrp"] = \
                                                    m["meas_result"]["rsrp"]
                                ue.rrc_meas[m["phys_cell_id"]]["rsrp"] = \
                                                    m["meas_result"]["rsrp"]
                            else:
                                self._meas[m["phys_cell_id"]]["rsrp"] = -139
                                ue.rrc_meas[m["phys_cell_id"]]["rsrp"] = -139

                            if "rsrq" in m["meas_result"]:
                                self._meas[m["phys_cell_id"]]["rsrq"] = \
                                                    m["meas_result"]["rsrq"]
                                ue.rrc_meas[m["phys_cell_id"]]["rsrq"] = \
                                                    m["meas_result"]["rsrq"]
                            else:
                                self._meas[m["phys_cell_id"]]["rsrq"] = -19
                                ue.rrc_meas[m["phys_cell_id"]]["rsrq"] = -19
                        else:
                            self._meas[m["phys_cell_id"]]["rsrp"] = -139
                            self._meas[m["phys_cell_id"]]["rsrq"] = -19
                            ue.rrc_meas[m["phys_cell_id"]]["rsrp"] = -139
                            ue.rrc_meas[m["phys_cell_id"]]["rsrq"] = -19

        self._meas_reply = meas

    def __eq__(self, other):

        return super().__eq__(other) and self.ue == other.ue and \
            self.meas_req == other.meas_req

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['ue'] = self.ue
        out['meas_req'] = self.meas_req
        out['meas_reply'] = self.meas_reply
        out['measurements'] = self.meas

        return out

    def run_once(self):
        """Send out RRC measurements request."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        tenant = RUNTIME.tenants[self.tenant_id]

        if self.ue not in tenant.ues:
            self.log.info("UE %s not found", self.ue)
            self.unload()
            return

        ue = tenant.ues[self.ue]

        if not ue.vbs.connection or ue.vbs.connection.stream.closed():
            self.log.info("VBS %s not connected", ue.vbs.addr)
            self.unload()
            return

        st_req = self.meas_req

        rrc_m_req = main_pb2.emage_msg()

        create_header(self.module_id, ue.vbs.enb_id, rrc_m_req.head)

        # Creating a trigger message to fetch UE's RRC measurements
        trigger_msg = rrc_m_req.te
        trigger_msg.action = main_pb2.EA_ADD

        rrc_m_msg = trigger_msg.mRRC_meas
        rrc_m_req_msg = rrc_m_msg.req

        rrc_m_req_msg.rnti = ue.rnti

        rrc_m_req_msg.rat = RRC_STATS_RAT_TYPE[st_req["rat_type"]]

        rrc_m_req_msg.measId = 0
        rrc_m_req_msg.m_obj.measObjId = 0
        rrc_m_req_msg.r_conf.reportConfId = 0

        if st_req["rat_type"] == "EUTRA":

            m_obj = rrc_m_req_msg.m_obj
            measObj_EUTRA = m_obj.measObj_EUTRA

            measObj_EUTRA.carrier_freq = st_req["carrier_freq"]
            measObj_EUTRA.meas_bw = RRC_STATS_BW[st_req["bandwidth"]]
            if "cells_to_measure" in st_req:
                for c in st_req["cells_to_measure"]:
                    measObj_EUTRA.cells.append(st_req["cells_to_measure"][c])
            if "blacklist_cells" in st_req:
                for c in st_req["blacklist_cells"]:
                    measObj_EUTRA.bkl_cells.append(st_req["blacklist_cells"][c])

        if st_req["rat_type"] == "EUTRA":
            # EUTRA report configuration

            r_conf = rrc_m_req_msg.r_conf
            rc_EUTRA = r_conf.rc_EUTRA

            # Setting default values
            rc_EUTRA.hysteresis = 0
            rc_EUTRA.trigg_time = configs_pb2.TTRIG_ms0
            rc_EUTRA.report_quant = configs_pb2.REPQ_BOTH
            rc_EUTRA.ue_rxtx_time_diff = configs_pb2.UERXTXTD_SETUP

            rc_EUTRA.trigg_quant = \
                RRC_STATS_TRIGGER_QUANT[st_req["trigger_quantity"]]
            rc_EUTRA.max_rep_cells = st_req["max_report_cells"]
            rc_EUTRA.rep_interval = \
                RRC_STATS_REPORT_INTR[st_req["report_interval"]]
            rc_EUTRA.rep_amount = \
                RRC_STATS_NUM_REPORTS[st_req["num_of_reports"]]

            if st_req["report_type"] == "periodical_ref_signal":
                rc_EUTRA.periodical.purpose = \
                    configs_pb2.PERRP_REPORT_STRONGEST_CELLS

            elif st_req["report_type"] == "A1":

                a1 = rc_EUTRA.a1

                if st_req["threshold1"]["type"] == "RSRP":
                    a1.a1_threshold.RSRP = st_req["threshold1"]["value"]
                else:
                    a1.a1_threshold.RSRQ = st_req["threshold1"]["value"]

            elif st_req["report_type"] == "A2":

                a2 = rc_EUTRA.a2

                if st_req["threshold1"]["type"] == "RSRP":
                    a2.a2_threshold.RSRP = st_req["threshold1"]["value"]
                else:
                    a2.a2_threshold.RSRQ = st_req["threshold1"]["value"]

            elif st_req["report_type"] == "A3":

                a3 = rc_EUTRA.a3

                a3.a3_offset = st_req["a3_offset"]
                a3.report_on_leave = 1

            elif st_req["report_type"] == "A4":

                a4 = rc_EUTRA.a4

                if st_req["threshold1"]["type"] == "RSRP":
                    a4.a4_threshold.RSRP = st_req["threshold1"]["value"]
                else:
                    a4.a4_threshold.RSRQ = st_req["threshold1"]["value"]

            elif st_req["report_type"] == "A5":

                a5 = rc_EUTRA.a5

                if st_req["threshold1"]["type"] == "RSRP":
                    a5.a5_threshold1.RSRP = st_req["threshold1"]["value"]
                else:
                    a5.a5_threshold1.RSRQ = st_req["threshold1"]["value"]

                if st_req["threshold2"]["type"] == "RSRP":
                    a5.a5_threshold2.RSRP = st_req["threshold2"]["value"]
                else:
                    a5.a5_threshold2.RSRQ = st_req["threshold2"]["value"]

        self.log.info("Sending RRC stats request to %s (id=%u)", ue.vbs.addr,
                      self.module_id)

        ue.vbs.connection.stream_send(rrc_m_req)

    def remove_measurement_from_vbs(self):
        """Remove this module."""

        self.log.info("Cleanup %s (id=%u)", self.module_type, self.module_id)

        vbses = RUNTIME.tenants[self.tenant_id].vbses

        if self.vbs not in vbses:
            return

        vbs = vbses[self.vbs]

        ue_addr = (self.vbs, self.ue)

        if ue_addr not in RUNTIME.tenants[self.tenant_id].ues:
            return

        ue = RUNTIME.tenants[self.tenant_id].ues[ue_addr]

        if not vbs.connection or vbs.connection.stream.closed():
            self.log.info("VBS %s not connected", vbs.addr)
            return

        meas = self.meas

        for m in meas.keys():
            if m in ue.rrc_meas:
                del ue.rrc_meas[m]

        rrc_m_req = main_pb2.emage_msg()

        create_header(self.module_id, ue.vbs.enb_id, rrc_m_req.head)

        # Creating a trigger message to delete UE's RRC measurements trigger
        trigger_msg = rrc_m_req.te
        trigger_msg.action = main_pb2.EA_DEL

        rrc_m_msg = trigger_msg.mRRC_meas
        rrc_m_req_msg = rrc_m_msg.req

        rrc_m_req_msg.rnti = ue.rnti
        rrc_m_req_msg.measId = 0
        rrc_m_req_msg.m_obj.measObjId = 0
        rrc_m_req_msg.r_conf.reportConfId = 0

        meas_req = self.meas_req
        rrc_m_req_msg.rat = RRC_STATS_RAT_TYPE[meas_req["rat_type"]]

        connection = vbs.connection
        enb_id = connection.vbs.enb_id

        vbs.connection.stream_send(rrc_m_req)

    def handle_response(self, response):
        """Handle an incoming stats response message.
        Args:
            message, a stats response message
        Returns:
            None
        """

        # update cache
        self.meas_reply = response

        # call callback
        self.handle_callback(self)


class VBSRRCStatsWorker(ModuleVBSPWorker):
    """ Counter worker. """

    def handle_ue_leave(self, ue):
        """Called when an UE disconnects from a VBS."""

        for module_id in list(self.modules.keys()):
            module = self.modules[module_id]
            if module.ue == ue.addr:
                module.unload()


def vbs_rrc_stats(**kwargs):
    """Create a new module."""

    return \
        RUNTIME.components[VBSRRCStatsWorker.__module__].add_module(**kwargs)


def bound_vbs_rrc_stats(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return vbs_rrc_stats(**kwargs)

setattr(EmpowerApp, VBSRRCStats.MODULE_NAME, bound_vbs_rrc_stats)


def launch():
    """ Initialize the module. """

    worker = VBSRRCStatsWorker(VBSRRCStats, PRT_VBSP_RRC_STATS)
    worker.pnfp_server.register_message(PRT_UE_LEAVE, None,
                                        worker.handle_ue_leave)

    return worker
