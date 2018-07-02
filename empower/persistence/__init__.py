#!/usr/bin/env python3
#
# Copyright (c) 2016 Roberto Riggio
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

"""Empower persistence layer."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker

from empower.settings import CONFIGDB_ENGINE

ENGINE = create_engine(CONFIGDB_ENGINE, pool_recycle=6000)


def on_connect(conn, record):
    conn.execute('pragma foreign_keys=ON')


event.listen(ENGINE, 'connect', on_connect)

SESSION_FACTORY = sessionmaker(autoflush=True,
                               bind=ENGINE,
                               expire_on_commit=False)
Session = scoped_session(SESSION_FACTORY)
