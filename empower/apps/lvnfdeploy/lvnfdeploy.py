#!/usr/bin/env python3
#
# Copyright (c) 2017 Roberto Riggio
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

"""Sample LVNF app."""


from empower.core.image import Image
from empower.core.app import EmpowerApp
from empower.core.app import DEFAULT_PERIOD


class LvnfDeploy(EmpowerApp):

    def __init__(self, **kwargs):
        EmpowerApp.__init__(self, **kwargs)
        self.cppup(callback=self.cpp_up_callback)
        self.lvnfjoin(callback=self.lvnf_join_callback)
        self.lvnfleave(callback=self.lvnf_leave_callback)

    def cpp_up_callback(self, cpp):
        """Called when a new cpp connects to the controller."""

        self.log.info("CPP %s connected!" % cpp.addr)

        # Create Image
        img = Image(vnf="in_0 -> Null() -> out_0")

        # Spawn LVNF
        self.spawn_lvnf(img, cpp)

    def lvnf_join_callback(self, lvnf):
        """Called when an LVNF associates to a tenant."""

        self.log.info("LVNF %s joined %s" % (lvnf.lvnf_id, lvnf.tenant_id))

        # Stop LVNF
        lvnf.stop()

    def lvnf_leave_callback(self, lvnf):
        """Called when an LVNF leaves a tennant."""

        self.log.info("LVNF %s stopped" % lvnf.lvnf_id)


def launch(tenant_id, every=DEFAULT_PERIOD):
    """ Initialize the module. """

    return LvnfDeploy(tenant_id=tenant_id, every=every)
