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

"""VBSP MAC statistics module."""

from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.vbspp.vbspserver import ModuleVBSPPWorker
from empower.core.module import Module
from protobuf_to_dict import protobuf_to_dict
from empower.main import RUNTIME
import empower.vbspp.messages.progran_pb2 as progran_pb2
import empower.vbspp.messages.header_pb2 as header_pb2
import empower.vbspp.messages.stats_messages_pb2 as stats_messages_pb2
from empower.vbspp import MAC_STATS_TYPE
from empower.vbspp import MAC_STATS_REPORT_FREQ
from empower.vbspp import MAC_CELL_STATS_TYPES
from empower.vbspp import MAC_UE_STATS_TYPES
from empower.vbspp import PRT_MAC_STATS_RESPONSE
from empower.vbspp import TIMER_IDS

import empower.logger
LOG = empower.logger.get_logger()


class VBSPMACStats(Module):
    """ MAC Statistics object. """

    MODULE_NAME = "vbsp_mac_stats"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'vbsp', 'mac_stats_req']

    # parameters
    _vbsp = None
    _mac_stats_req = None
    _mac_stats_reply = None

    def __eq__(self, other):

        return super().__eq__(other) and False

    @property
    def vbsp(self):
        """Return VBSP."""

        return self._vbsp

    @vbsp.setter
    def vbsp(self, value):
        """Set VBSP."""

        self._vbsp = EtherAddress(value)

    @property
    def mac_stats_req(self):
        """Return configuration of mac stats requested."""

        return self._mac_stats_req

    @mac_stats_req.setter
    def mac_stats_req(self, value):
        """Set configuration of mac stats requested."""

        self._mac_stats_req = value

    @property
    def mac_stats_reply(self):
        """Return MAC stats reply."""

        return self._mac_stats_reply

    @mac_stats_reply.setter
    def mac_stats_reply(self, response):
        """Set MAC stats reply."""

        self._mac_stats_reply = protobuf_to_dict(response)

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['vbsp'] = self.vbsp
        out['mac_stats_req'] = self.mac_stats_req
        out['mac_stats'] = self.mac_stats_reply

        return out

    def run_once(self):
        """ Send out mac stats request. """

        print("CIAOO")

        if self.tenant_id not in RUNTIME.tenants:
            return

        vbsps = RUNTIME.tenants[self.tenant_id].vbsps

        if self.vbsp not in vbsps:
            return

        vbsp = vbsps[self.vbsp]

        if not vbsp.connection:
            return

        print("xxx")

        stats_request = progran_pb2.progran_message()

        stats_request_config = self.mac_stats_req["stats_request_config"]
        stats_request_msg = stats_request.stats_request_msg
        stats_request_msg.type = \
            MAC_STATS_TYPE[stats_request_config["report_type"]]

        connection = vbsp.connection

        if stats_request_config["report_frequency"] == "off":
            connection.create_header(stats_request_config["timer_xid"], connection.enb_id, header_pb2.PRPT_GET_ENB_CONFIG_REQUEST, stats_request.stats_request_msg.header)
        else:
            connection.create_header(self.module_id, connection.enb_id, header_pb2.PRPT_GET_ENB_CONFIG_REQUEST, stats_request.stats_request_msg.header)

        stats_request.msg_dir = progran_pb2.INITIATING_MESSAGE

        if stats_request_config["report_frequency"] == "periodical":
            TIMER_IDS.append(self.module_id)

        if stats_request_msg.type == stats_messages_pb2.PRST_COMPLETE_STATS:

            complete_stats = stats_request_msg.complete_stats_request
            complete_stats.report_frequency = MAC_STATS_REPORT_FREQ[stats_request_config["report_frequency"]]
            complete_stats.sf = stats_request_config["periodicity"]

            cc_report_flag = 0
            ue_report_flag = 0

            if stats_request_config["report_frequency"] != "off":
                for flag in stats_request_config["report_config"]["cell_report_type"]["cell_report_flags"]:
                    cc_report_flag |= MAC_CELL_STATS_TYPES[flag]

                for flag in stats_request_config["report_config"]["ue_report_type"]["ue_report_flags"]:
                    ue_report_flag |= MAC_UE_STATS_TYPES[flag]

            complete_stats.ue_report_flags = ue_report_flag
            complete_stats.cell_report_flags = cc_report_flag

        elif stats_request_msg.type == stats_messages_pb2.PRST_CELL_STATS:
            cell_stats = stats_request_msg.cell_stats_request
            cell_stats.report_frequency = MAC_STATS_REPORT_FREQ[stats_request_config["report_frequency"]]
            cell_stats.sf = stats_request_config["periodicity"]

            cc_report_flag = 0

            for flag in stats_request_config["report_config"]["cell_report_type"]["cell_report_flags"]:
                cc_report_flag |= MAC_CELL_STATS_TYPES[flag]

            for cc in stats_request_config["report_config"]["cell_report_type"]["cc_id"]:
                cell_stats.cell.append(cc)

            cell_stats.flags = cc_report_flag

        elif stats_request_msg.type == stats_messages_pb2.PRST_UE_STATS:
            ue_stats = stats_request_msg.ue_stats_request
            ue_stats.report_frequency = MAC_STATS_REPORT_FREQ[stats_request_config["report_frequency"]]
            ue_stats.sf = stats_request_config["periodicity"]

            ue_report_flag = 0

            for flag in stats_request_config["report_config"]["ue_report_type"]["ue_report_flags"]:
                ue_report_flag |= MAC_UE_STATS_TYPES[flag]

            for rnti in stats_request_config["report_config"]["ue_report_type"]["ue_rnti"]:
                ue_stats.rnti.append(rnti)

            ue_stats.flags = ue_report_flag

        self.log.info("Sending mac stats request to %s (id=%u)", vbsp.addr,
                      self.module_id)

        vbsp.connection.stream_send(stats_request)

        if stats_request_config["report_frequency"] == "off":
            self.worker.remove_module(stats_request_config["timer_xid"])

    def handle_response(self, response):
        """Handle an incoming PRT_MAC_STATS_RESPONSE message.
        Args:
            response, a PRT_MAC_STATS_RESPONSE message
        Returns:
            None
        """

        # update cache
        self.mac_stats_reply = response

        print(response.__str__())

        # call callback
        self.handle_callback(self)


class VBSPMACStatsWorker(ModuleVBSPPWorker):
    """ Counter worker. """

    pass


def vbsp_mac_stats(**kwargs):
    """Create a new module."""

    return \
        RUNTIME.components[VBSPMACStatsWorker.__module__].add_module(**kwargs)


def bound_vbsp_mac_stats(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return vbsp_mac_stats(**kwargs)

setattr(EmpowerApp, VBSPMACStats.MODULE_NAME, bound_vbsp_mac_stats)


def launch():
    """ Initialize the module. """

    return VBSPMACStatsWorker(VBSPMACStats, PRT_MAC_STATS_RESPONSE)
