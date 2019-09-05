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

"""Base worker class."""

from empower.core.service import EService

EVERY = 2000


class EWorker(EService):
    """Base worker class."""

    def __init__(self, service_id, project_id, **kwargs):

        if 'every' not in kwargs:
            kwargs['every'] = EVERY

        super().__init__(service_id=service_id,
                         project_id=project_id,
                         **kwargs)
