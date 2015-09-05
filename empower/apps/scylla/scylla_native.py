#!/usr/bin/env python3
#
# Copyright (c) 2015, Roberto Riggio
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CREATE-NET nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CREATE-NET ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CREATE-NET BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""EmPOWER application implementing a basic mobility manager."""

import uuid

from empower.core.app import EmpowerApp
from empower.core.app import EmpowerAppHandler
from empower.core.app import EmpowerAppHomeHandler
from empower.core.app import DEFAULT_PERIOD

import empower.logger
LOG = empower.logger.get_logger()

VNF = """in_0
-> Classifier(12/bbbb)
-> Strip(14)
-> dupe::ScyllaWifiDupeFilter()
-> WifiDecap()
-> out_0;"""


class ScyllaHandler(EmpowerAppHandler):
    pass


class ScyllaHomeHandler(EmpowerAppHomeHandler):
    pass


class Scylla(EmpowerApp):
    """EmPOWER application implementing an uplink/downlink decoupling system.

    Command Line Parameters:

        period: loop period in ms (optional, default 5000ms)

    Example:

        ./empower.py apps.decoupled.decoupled:EmPOWER --period=5000

    """

    MODULE_NAME = "scylla"
    MODULE_HANDLER = ScyllaHandler
    MODULE_HOME_HANDLER = ScyllaHomeHandler

    def __init__(self, tenant_id, period):

        EmpowerApp.__init__(self, tenant_id, period)

        self.lvnf = None

        # fix lvnf id
        self.lvnf_id = uuid.UUID("20c7ecf7-be9e-4643-8f98-8ac582b4bc03")

        # create image
        handlers = [["dupes_table", "dupe.dupes_table"]]
        state_handlers = ["dupes_table"]
        self.image = self.tenant.add_image(tenant_id=tenant_id,
                                           desc="Duplicates Filtering",
                                           nb_ports=1,
                                           vnf=VNF,
                                           handlers=handlers,
                                           state_handlers=state_handlers)

        # register cpp up callback
        self.cppup(callback=self.cpp_up_callback)

    def cpp_up_callback(self, cpp):

        # lvnf already deployed, ignore event
        if self.lvnf:
            return

        # create LVNF
        self.lvnf = self.tenant.add_lvnf(lvnf_id=self.lvnf_id,
                                         image=self.image,
                                         cpp=cpp)

        # register lvnf join callback
        self.lvnfjoin(callback=self.lvnf_join_callback)

        # register lvnf leave callback
        self.lvnfleave(callback=self.lvnf_leave_callback)

    def lvnf_join_callback(self, lvnf):

        # call handler
        lvnf.in_0_count(callback=self.count_callback, every=5000)

        # call handler
        lvnf.out_0_count(callback=self.count_callback, every=5000)

        # call handler
        lvnf.dupes_table(callback=self.dupes_callback, every=5000)

    def lvnf_leave_callback(self, lvnf):

        # reset lvnf
        if lvnf == self.lvnf:
            self.lvnf = None

    def count_callback(self, handler):

        LOG.info("Counted a total of %u packets." % int(handler.samples[0]))

    def dupes_callback(self, handler):

        LOG.info("Duplicates table:\n%s" % "\n".join(handler.samples))

    def loop(self):
        """Periodic control loop."""

        pass


def launch(tenant, period=DEFAULT_PERIOD):
    """ Initialize the module. """

    return Scylla(tenant, period)
