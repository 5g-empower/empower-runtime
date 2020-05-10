#!/usr/bin/env python3
#
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

"""List projects."""

import empower_core.command as command


def do_cmd(gargs, *_):
    """List projects. """

    _, data = command.connect(gargs, ('GET', '/api/v1/projects'), 200)

    for entry in data.values():

        accum = []

        accum.append("project_id ")

        accum.append(entry['project_id'])

        accum.append(" desc \"%s\"" % entry['desc'])

        if 'wifi_props' in entry and entry['wifi_props']:
            accum.append(" ssid \"%s\"" % entry['wifi_props']['ssid'])

        if 'lte_props' in entry and entry['lte_props']:
            accum.append(" plmnid \"%s\"" % entry['lte_props']['plmnid'])

        print(''.join(accum))
