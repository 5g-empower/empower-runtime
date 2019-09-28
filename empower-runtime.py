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

"""Launch the 5G-EmPOWER Runtime."""

from empower.main import main


if __name__ == "__main__":

    # Default modules
    ARGVS = [
        'managers.persistencymanager.persistencymanager',
        'managers.envmanager.envmanager',
        'managers.apimanager.apimanager',
        'managers.accountsmanager.accountsmanager',
        'managers.projectsmanager.projectsmanager',
        'managers.ranmanager.lvapp.lvappmanager',
        'managers.ranmanager.vbsp.vbspmanager',
        'managers.timeseriesmanager.timeseriesmanager'
    ]

    main(ARGVS)
