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
from empower.vbsp.messages import configs_pb2
from empower.vbsp.messages import main_pb2
from empower.core.app import EmpowerApp
from empower.datatypes.etheraddress import EtherAddress
from empower.core.module import ModuleTrigger
from empower.vbsp.vbspserver import ModuleVBSPWorker
from empower.ue_confs import REQ_EVENT_TYPE
from empower.vbsp import PRT_VBSP_RRC_MEAS_CONF
from empower.vbsp.vbspconnection import create_header
from empower.vbsp import PRT_UE_LEAVE
from empower.core.utils import ether_to_hex

from empower.main import RUNTIME


class UERRCMeasConfs(ModuleTrigger):
    """ UERRCMeasConfs object. """

    MODULE_NAME = "ue_rrc_meas_confs"
    REQUIRED = ['module_type', 'worker', 'tenant_id', 'ue', 'conf_req']

    def __init__(self):

        ModuleTrigger.__init__(self)

        # parameters
        self._ue = None
        self._conf_req = None
        self._conf_reply = None

    @property
    def ue(self):
        """Return UE."""

        return self._ue

    @ue.setter
    def ue(self, value):
        """Set UE."""

        self._ue = EtherAddress(value)

    @property
    def conf_req(self):
        """Return request given for RRC measurements configuration of UE."""

        return self._conf_req

    @conf_req.setter
    def conf_req(self, value):
        """Set request parameter given for RRC measurements configuration."""

        if self.conf_req:
            raise ValueError("Cannot update configuration")

        if "event_type" not in value:
            raise ValueError("Missing event type (trigger, schedule, single)")

        if value["event_type"] not in REQ_EVENT_TYPE:
            raise ValueError("Invalid event type (trigger, schedule, single)")

        if value["event_type"] == "schedule" and "periodicity" not in value:
            raise ValueError("Missing periodicity for scheduled event")

        self._conf_req = value

    @property
    def conf_reply(self):
        """Return RRC measurements configuration reply."""

        return self._conf_reply

    @conf_reply.setter
    def conf_reply(self, response):
        """Set RRC measurements configuration reply."""

        self._conf_reply = protobuf_to_dict(response)
        reply = protobuf_to_dict(response)

        ue = RUNTIME.tenants[self.tenant_id].ues[self.ue]

        event_type = response.WhichOneof("event_types")
        conf = reply[event_type]["mUE_rrc_meas_conf"]["repl"]
        self._conf_reply = \
            self._conf_reply[event_type]["mUE_rrc_meas_conf"]["repl"]

        if conf["status"] != configs_pb2.CREQS_SUCCESS:
            return

        del conf["rnti"]
        del conf["status"]

        if "ue_rrc_state" in conf:
            ue.rrc_state = conf["ue_rrc_state"]
            del conf["ue_rrc_state"]

        if "capabilities" in conf:
            ue.capabilities = conf["capabilities"]
            del conf["capabilities"]

        ue.rrc_meas_config = conf

    def __eq__(self, other):

        return super().__eq__(other) and self.ue == other.ue and \
            self.conf_req == other.conf_req

    def to_dict(self):
        """ Return a JSON-serializable."""

        out = super().to_dict()

        out['ue'] = self.ue
        out['conf_req'] = self.conf_req
        out['conf_reply'] = self.conf_reply

        return out

    def run_once(self):
        """Send out RRC measurements configuration request."""

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

        cf_req = self.conf_req

        rrc_m_conf_req = main_pb2.emage_msg()

        create_header(self.module_id, ue.vbs.enb_id, rrc_m_conf_req.head)

        # Creating a message to fetch UEs RRC measurement configuration
        event_type_msg = None
        if cf_req["event_type"] == "trigger":
            event_type_msg = rrc_m_conf_req.te
            event_type_msg.action = main_pb2.EA_ADD
        elif cf_req["event_type"] == "schedule":
            event_type_msg = rrc_m_conf_req.sche
            event_type_msg.action = main_pb2.EA_ADD
            event_type_msg.interval = cf_req["periodicity"]
        else:
            event_type_msg = rrc_m_conf_req.se

        rrc_m_conf_msg = event_type_msg.mUE_rrc_meas_conf
        rrc_m_conf_req_msg = rrc_m_conf_msg.req

        rrc_m_conf_req_msg.rnti = ue.rnti

        self.log.info("Sending UEs RRC meas. config req to %s (id=%u)",
                      ue.vbs.addr, self.module_id)

        ue.vbs.connection.stream_send(rrc_m_conf_req)

    def remove_trigger_from_vbs(self):
        """Remove this module."""

        self.log.info("UEs RRC meas. config Cleanup %s (id=%u)",
                      self.module_type, self.module_id)

        ue = RUNTIME.tenants[self.tenant_id].ues[self.ue]

        if not ue.vbs.connection or ue.vbs.connection.stream.closed():
            self.log.info("VBS %s not connected", ue.vbs.addr)
            self.unload()
            return

        cf_req = self.conf_req

        rrc_m_conf_req = main_pb2.emage_msg()

        create_header(self.module_id, ue.vbs.enb_id, rrc_m_conf_req.head)

        # Creating a message to fetch UEs RRC measurement configuration
        event_type_msg = None
        if cf_req["event_type"] == "trigger":
            event_type_msg = rrc_m_conf_req.te
            event_type_msg.action = main_pb2.EA_DEL
        elif cf_req["event_type"] == "schedule":
            event_type_msg = rrc_m_conf_req.sche
            event_type_msg.action = main_pb2.EA_DEL
        else:
            return

        rrc_m_conf_msg = event_type_msg.mUE_rrc_meas_conf
        rrc_m_conf_req_msg = rrc_m_conf_msg.req

        rrc_m_conf_req_msg.rnti = ue.rnti

        self.log.info("Sending UEs Del RRC meas. config req to %s (id=%u)",
                      ue.vbs.addr, self.module_id)

        ue.vbs.connection.stream_send(rrc_m_conf_req)

    def handle_response(self, response):
        """Handle an incoming stats response message.
        Args:
            message, a stats response message
        Returns:
            None
        """

        # update cache
        self.conf_reply = response

        # call callback
        self.handle_callback(self)


class UERRCMeasConfsWorker(ModuleVBSPWorker):
    """ UERRCMeasConfsWorker worker. """

    def handle_ue_leave(self, ue):
        """Called when an UE disconnects from a VBS."""

        for module_id in list(self.modules.keys()):
            module = self.modules[module_id]
            if module.ue == ue.addr:
                module.unload()


def ue_rrc_meas_confs(**kwargs):
    """Create a new module."""

    module = RUNTIME.components[UERRCMeasConfsWorker.__module__]
    return module.add_module(**kwargs)


def bound_ue_rrc_meas_confs(self, **kwargs):
    """Create a new module (app version)."""

    kwargs['tenant_id'] = self.tenant.tenant_id
    return ue_rrc_meas_confs(**kwargs)

setattr(EmpowerApp, UERRCMeasConfs.MODULE_NAME, bound_ue_rrc_meas_confs)


def launch():
    """ Initialize the module. """

    worker = UERRCMeasConfsWorker(UERRCMeasConfs, PRT_VBSP_RRC_MEAS_CONF)
    worker.pnfp_server.register_message(PRT_UE_LEAVE, None,
                                        worker.handle_ue_leave)

    return worker
