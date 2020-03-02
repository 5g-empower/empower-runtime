#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi:ts=4:et

import ssl
from pymodm.connection import connect

from empower.managers.lommmanager.lnsdp.lnsdpmanager import LNSDPManager

DEFAULT_URI = "mongodb://localhost:27017/empower"

connect(DEFAULT_URI, ssl_cert_reqs=ssl.CERT_NONE)
print("Connected to MongoDB: %s" % DEFAULT_URI)

