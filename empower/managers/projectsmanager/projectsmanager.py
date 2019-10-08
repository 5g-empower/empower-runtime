#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
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

"""Projects manager."""

import empower.apps
import empower.primitives
import empower.tutorials

from empower.main import srv_or_die
from empower.core.service import EService

from empower.managers.projectsmanager.project import Project
from empower.managers.projectsmanager.project import EmbeddedWiFiProps
from empower.managers.projectsmanager.project import EmbeddedLTEProps
from empower.managers.projectsmanager.project import T_BSSID_TYPE_SHARED
from empower.managers.projectsmanager.project import T_BSSID_TYPE_UNIQUE

from empower.managers.projectsmanager.cataloghandler import CatalogHandler
from empower.managers.projectsmanager.appshandler import AppsHandler
from empower.managers.projectsmanager.appshandler import AppAttributesHandler

from empower.managers.projectsmanager.projectshandler import ProjectsHandler, \
    ProjectsWiFiSlicesHandler, ProjectsLTESlicesHandler, ProjectLVAPsHandler


class ProjectsManager(EService):
    """Projects manager."""

    HANDLERS = [CatalogHandler, AppsHandler, AppAttributesHandler,
                ProjectsHandler, ProjectsWiFiSlicesHandler,
                ProjectsLTESlicesHandler, ProjectLVAPsHandler]

    projects = {}
    accounts_manager = None

    def start(self):
        """Start projects manager."""

        super().start()

        self.accounts_manager = \
            srv_or_die("empower.managers.accountsmanager.accountsmanager")

        for project in Project.objects.all():
            self.projects[project.project_id] = project
            self.projects[project.project_id].start_services()

    @property
    def catalog(self):
        """Return available apps."""

        results = {}

        results.update(self.walk_module(empower.apps))
        results.update(self.walk_module(empower.primitives))
        results.update(self.walk_module(empower.tutorials))

        return results

    def load_project_by_ssid(self, ssid):
        """Find a project by SSID."""

        for project in self.projects.values():
            if not project.wifi_props:
                continue
            if project.wifi_props.ssid == ssid:
                break
        else:
            project = None

        return project

    def load_project_by_plmnid(self, plmnid):
        """Find a project by SSID."""

        for project in self.projects.values():
            if not project.lte_props:
                continue
            if project.lte_props.plmnid == plmnid:
                break
        else:
            project = None

        return project

    def get_available_ssids(self, sta, block):
        """Return the list of available networks for the specified sta."""

        networks = list()

        for project in self.projects.values():

            if not project.wifi_props:
                continue

            if sta not in project.wifi_props.allowed:
                continue

            if project.wifi_props.bssid_type == T_BSSID_TYPE_SHARED:

                bssid = project.generate_bssid(block.hwaddr)
                ssid = project.wifi_props.ssid
                networks.append((bssid, ssid))

            elif project.wifi_props.bssid_type == T_BSSID_TYPE_UNIQUE:

                bssid = project.generate_bssid(sta)
                ssid = project.wifi_props.ssid
                networks.append((bssid, ssid))

            else:

                self.log.error("Invalid BSSID type: %s",
                               project.wifi_props.bssid_type)

        return networks

    def create(self, desc, project_id, owner, wifi_props=None, lte_props=None):
        """Create new project."""

        if project_id in self.projects:
            raise ValueError("Project %s already defined" % project_id)

        if owner not in self.accounts_manager.accounts:
            raise ValueError("Undefined account %s" % owner)

        project = Project(project_id=project_id, desc=desc, owner=owner)

        if wifi_props:
            project.wifi_props = EmbeddedWiFiProps(**wifi_props)

        if lte_props:
            project.lte_props = EmbeddedLTEProps(**lte_props)

        project.save()

        self.projects[project_id] = project

        project.upsert_wifi_slice(slice_id=0)

        project.upsert_lte_slice(slice_id=0)

        self.projects[project_id].start_services()

        return self.projects[project_id]

    def update(self, project_id, wifi_props=None, lte_props=None):
        """Update project."""

        if project_id not in self.projects:
            raise ValueError("Project %s not available" % project_id)

        project = self.projects[project_id]

        try:

            # not all wifi props can be modified
            if wifi_props:

                if "allowed" in wifi_props:
                    project.wifi_props.allowed = wifi_props["allowed"]

            # not all lte props can be modified
            if lte_props:
                pass

            project.save()

        finally:

            project.refresh_from_db()

        return self.projects[project_id]

    def remove_all(self):
        """Remove all projects."""

        for project_id in list(self.projects):
            self.remove(project_id)

    def remove(self, project_id):
        """Remove project."""

        # Check if project exists
        if project_id not in self.projects:
            raise KeyError("%s not registered" % project_id)

        # Fetch project
        project = self.projects[project_id]

        # Remove hosted LVAPs
        for lvap in list(project.lvaps.values()):

            # The LVAP is associated
            if lvap.ssid and lvap.wtp.connection:
                lvap.wtp.connection.send_lvap_leave_message_to_self(lvap)

            # Reset the LVAP
            del lvap.wtp.connection.manager.lvaps[lvap.addr]
            lvap.clear_blocks()

        # Remove hosted VAPs
        for vap in list(project.vaps.values()):

            # Reset the LVAP
            del vap.wtp.connection.manager.vaps[vap.addr]
            vap.clear_block()

        # Stop running services
        self.projects[project_id].stop_services()

        # Delete project from datase and manager
        project.delete()
        del self.projects[project_id]


def launch(**kwargs):
    """Start projects manager."""

    return ProjectsManager(**kwargs)
