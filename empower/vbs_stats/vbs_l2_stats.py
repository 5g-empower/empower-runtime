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

"""VBS Stats Module."""

from protobuf_to_dict import protobuf_to_dict

from empower.vbsp.messages import statistics_pb2
from empower.vbsp.messages import main_pb2
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.core.module import Module
from empower.vbs_stats import L2_STATS_TYPE
from empower.vbs_stats import L2_CELL_STATS_TYPES
from empower.vbs_stats import L2_STATS_REPORT_FREQ
from empower.vbs_stats import L2_UE_STATS_TYPES
from empower.vbsp.vbspconnection import create_header
from empower.vbs_stats import PRT_VBSP_L2_STATS_RESPONSE
from empower.main import RUNTIME


class VBSL2Stats(Module):
    """ VBSL2Stats object. """

    MODULE_NAME = "vbs_l2_stats"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'vbs', 'l2_stats_req']

    def __init__(self):

        Module.__init__(self)

        # parameters
        self.every = -1
        self._vbs = None
        self._l2_stats_req = None
        self._l2_stats_reply = None

    @property
    def vbs(self):
        """Return VBS."""

        return self._vbs

    @vbs.setter
    def vbs(self, value):
        """Set VBSP."""

        self._vbs = EtherAddress(value)

    @property
    def l2_stats_req(self):
        """Return configuration of layer 2 stats requested."""

        return self._l2_stats_req

    @l2_stats_req.setter
    def l2_stats_req(self, value):
        """Set configuration of layer 2 stats requested."""

        if self.l2_stats_req:
            raise ValueError("Cannot update configuration")

        if "report_type" not in value:
            raise ValueError("Missing report_type element")

        if value["report_type"] not in L2_STATS_TYPE:
            raise ValueError("Invalid report_type element")

        if "report_frequency" not in value:
            raise ValueError("Missing report_frequency element")

        if value["report_frequency"] not in L2_STATS_REPORT_FREQ:
            raise ValueError("Invalid report_frequency element")

        if value["report_frequency"] == "periodical":
            if "periodicity" not in value:
                raise ValueError("Missing periodicity element")

        if "report_config" not in value:
            raise ValueError("Missing report_config element")

        if value["report_type"] != "cell":

            if "ue_report_type" not in value["report_config"]:
                raise ValueError("Missing ue_report_type element")

            ue_report_type = value["report_config"]["ue_report_type"]

            if value["report_type"] == "ue" and \
                "ue_rnti" not in ue_report_type:
                raise ValueError("missing ue_rnti element")

            if "ue_report_flags" not in ue_report_type:
                raise ValueError("Missing ue_report_flags element")

            if len(ue_report_type["ue_report_flags"]) == 0:
                raise ValueError("Invalid ue_report_flags element")

            for flag in ue_report_type["ue_report_flags"]:
                if flag not in L2_UE_STATS_TYPES:
                    raise ValueError("Invalid ue_report_flag type")

        if value["report_type"] != "ue":

            if "cell_report_type" not in value["report_config"]:
                raise ValueError("missing cell_report_type element")

            cell_report_type = value["report_config"]["cell_report_type"]

            if value["report_type"] == "cell" and \
                "cc_id" not in cell_report_type:
                raise ValueError("missing cc_id element")

            if "cell_report_flags" not in cell_report_type:
                raise ValueError("missing cell_report_flags element")

            if len(cell_report_type) == 0:
                raise ValueError("invalid cell_report_flags element")

            for flag in cell_report_type['cell_report_flags']:
                if flag not in L2_CELL_STATS_TYPES:
                    raise ValueError("Invalid cell_report_flag type")

        self._l2_stats_req = value

    @property
    def l2_stats_reply(self):
        """Return layer 2 stats reply."""

        return self._l2_stats_reply

    @l2_stats_reply.setter
    def l2_stats_reply(self, response):
        """Set layer 2 stats reply."""

        self._l2_stats_reply = protobuf_to_dict(response)

    def __eq__(self, other):

        return super().__eq__(other) and self.vbs == other.vbs and \
            self.l2_stats_req == other.l2_stats_req

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['vbs'] = self.vbs
        out['l2_stats_req'] = self.l2_stats_req
        out['l2_stats'] = self.l2_stats_reply

        return out

    def run_once(self):
        """Send out vbs layer 2 stats request."""

        if self.tenant_id not in RUNTIME.tenants:
            self.log.info("Tenant %s not found", self.tenant_id)
            self.unload()
            return

        vbses = RUNTIME.tenants[self.tenant_id].vbses

        if self.vbs not in vbses:
            return

        vbs = vbses[self.vbs]

        if not vbs.connection or vbs.connection.stream.closed():
            self.log.info("VBS %s not connected", vbs.addr)
            return

        st_req_conf = self.l2_stats_req
        rep_conf = st_req_conf["report_config"]

        st_req = main_pb2.emage_msg()
        st_req_msg = st_req.mStats
        st_req_msg.type = statistics_pb2.L2_STATISTICS_REQUEST
        l2_st_req = st_req_msg.l2_stats_req
        l2_st_req.type = \
            L2_STATS_TYPE[st_req_conf["report_type"]]
        l2_st_req.report_freq = \
            L2_STATS_REPORT_FREQ[st_req_conf["report_frequency"]]

        l2_st_req.subframe = 0
        cc_report_flag = 0
        ue_report_flag = 0

        connection = vbs.connection
        enb_id = connection.vbs.enb_id

        create_header(self.module_id, enb_id, main_pb2.STATS_REQ, st_req.head)

        if st_req_conf["report_frequency"] == "periodical":
            l2_st_req.subframe = st_req_conf["periodicity"]

        if l2_st_req.type == statistics_pb2.L2ST_COMPLETE:

            comp_st = l2_st_req.comp_stats_req

            for flag in rep_conf["cell_report_type"]["cell_report_flags"]:
                cc_report_flag |= L2_CELL_STATS_TYPES[flag]

            for flag in rep_conf["ue_report_type"]["ue_report_flags"]:
                ue_report_flag |= L2_UE_STATS_TYPES[flag]

            comp_st.ue_report_flags = ue_report_flag
            comp_st.cell_report_flags = cc_report_flag

        elif l2_st_req.type == statistics_pb2.L2ST_CELL:

            cell_st = l2_st_req.cell_stats_req

            for flag in rep_conf["cell_report_type"]["cell_report_flags"]:
                cc_report_flag |= L2_CELL_STATS_TYPES[flag]

            for c_carrier in rep_conf["cell_report_type"]["cc_id"]:
                cell_st.cc_id.append(c_carrier)

            cell_st.report_flags = cc_report_flag

        elif l2_st_req.type == statistics_pb2.L2ST_UE:

            ue_st = l2_st_req.ue_stats_req

            for flag in rep_conf["ue_report_type"]["ue_report_flags"]:
                ue_report_flag |= L2_UE_STATS_TYPES[flag]

            for rnti in rep_conf["ue_report_type"]["ue_rnti"]:
                ue_st.rnti.append(rnti)

            ue_st.report_flags = ue_report_flag

        self.log.info("Sending layer 2 stats request to %s (id=%u)", vbs.addr,
                      self.module_id)

        vbs.connection.stream_send(st_req)

    def cleanup(self):
        """Remove this module."""

        self.log.info("Cleanup %s (id=%u)", self.module_type, self.module_id)

        vbses = RUNTIME.tenants[self.tenant_id].vbses

        if self.vbs not in vbses:
            return

        vbs = vbses[self.vbs]

        if not vbs.connection or vbs.connection.stream.closed():
            self.log.info("VBS %s not connected", vbs.addr)
            return

        st_req = main_pb2.emage_msg()
        st_req_msg = st_req.mStats
        st_req_msg.type = statistics_pb2.L2_STATISTICS_REQUEST
        l2_st_req = st_req_msg.l2_stats_req
        l2_st_req.report_freq = statistics_pb2.REPF_OFF

        connection = vbs.connection
        enb_id = connection.vbs.enb_id

        create_header(self.module_id, enb_id, main_pb2.STATS_REQ, st_req.head)

        vbs.connection.stream_send(st_req)

    def handle_response(self, response):
        """Handle an incoming stats response message.
        Args:
            message, a stats response message
        Returns:
            None
        """

        # update cache
        self.l2_stats_reply = response

        # call callback
        self.handle_callback(self)


class VBSL2StatsWorker(ModuleVBSPWorker):
    """ Counter worker. """

    pass


def vbs_stats(**kwargs):
    """Create a new module."""

    return RUNTIME.components[VBSL2StatsWorker.__module__].add_module(**kwargs)


def bound_vbs_stats(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return vbs_stats(**kwargs)

setattr(EmpowerApp, VBSL2Stats.MODULE_NAME, bound_vbs_stats)


def launch():
    """ Initialize the module. """

    return VBSL2StatsWorker(VBSL2Stats, PRT_VBSP_L2_STATS_RESPONSE)
