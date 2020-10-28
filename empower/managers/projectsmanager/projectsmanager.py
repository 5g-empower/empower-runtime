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

from pymodm.errors import ValidationError

from empower_core.projectsmanager.projectsmanager import ProjectsManager

from empower_core.projectsmanager.appcallbackhandler import \
    AppCallbacksHandler
from empower_core.projectsmanager.cataloghandler import CatalogHandler
from empower_core.projectsmanager.appshandler import AppsHandler

from empower.managers.projectsmanager.projectshandler import ProjectsHandler
from empower.managers.projectsmanager.project import EmpowerProject
from empower.managers.projectsmanager.project import EmbeddedWiFiProps
from empower.managers.projectsmanager.project import EmbeddedLTEProps
from empower.managers.projectsmanager.project import T_BSSID_TYPE_SHARED
from empower.managers.projectsmanager.project import T_BSSID_TYPE_UNIQUE
from empower.managers.projectsmanager.projectswifiaclhandler import \
    ProjectsWiFiACLHandler
from empower.managers.projectsmanager.projectswifisliceshandler import \
    ProjectsWiFiSlicesHandler
from empower.managers.projectsmanager.projectsltesliceshandler import \
    ProjectsLTESlicesHandler
from empower.managers.projectsmanager.projectslvapshandler import \
    ProjectsLVAPsHandler
from empower.managers.projectsmanager.projectsusershandler import \
    ProjectsUsersHandler


class EmpowerProjectsManager(ProjectsManager):
    """Projects manager."""

    HANDLERS = [CatalogHandler, AppsHandler, ProjectsLVAPsHandler,
                ProjectsHandler, ProjectsWiFiACLHandler,
                ProjectsWiFiSlicesHandler, ProjectsLTESlicesHandler,
                AppCallbacksHandler, ProjectsUsersHandler]

    PROJECT_IMPL = EmpowerProject

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
        """Find a project by PLMNID."""

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

            if str(sta) not in project.wifi_props.allowed:
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

        project = super().create(desc=desc, project_id=project_id, owner=owner)

        try:

            if wifi_props:
                project.wifi_props = EmbeddedWiFiProps(**wifi_props)

            if lte_props:
                project.lte_props = EmbeddedLTEProps(**lte_props)

            project.save()

            project.upsert_wifi_slice(slice_id=0)
            project.upsert_lte_slice(slice_id=0)

        except ValueError as ex:
            self.remove(project.project_id)
            raise ValueError(ex)

        except ValidationError as ex:
            self.remove(project.project_id)
            raise ValueError(ex)

        return self.projects[project_id]

    def remove(self, project_id):
        """Remove project."""

        # Check if project exists
        if project_id not in self.projects:
            raise KeyError("Project %s not registered" % project_id)

        # Fetch project
        project = self.projects[project_id]

        # Remove hosted LVAPs
        for lvap in list(project.lvaps.values()):

            # The LVAP is associated
            if lvap.ssid and lvap.wtp.connection:
                lvap.wtp.connection.send_client_leave_message_to_self(lvap)

            # Reset the LVAP
            del lvap.wtp.connection.manager.lvaps[lvap.addr]
            lvap.clear_blocks()

        # Remove hosted UEs
        for user in list(project.users.values()):

            # The UEs is associated
            if user.plmnid and user.vbs.connection:
                user.vbs.connection.send_client_leave_message_to_self(user)

            # Reset the LVAP
            del user.vbs.connection.manager.users[user.imsi]

        # Remove hosted VAPs
        for vap in list(project.vaps.values()):

            # Reset the LVAP
            del vap.wtp.connection.manager.vaps[vap.bssid]
            vap.clear_block()

        # Remove project
        super().remove(project_id)


def launch(context, service_id, catalog_packages):
    """ Initialize the module. """

    return EmpowerProjectsManager(context=context, service_id=service_id,
                                  catalog_packages=catalog_packages)
