#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi:ts=4:et

import pycurl
try:
    from io import BytesIO # python3
except ImportError:
    from StringIO import StringIO as BytesIO
import json

USERNAME  = 'foo'
PASSWORD  = 'foo'
URI_LNSS  = 'http://localhost:8888/api/v1/lnsd/lnss'
URI_LGTWS = 'http://localhost:8888/api/v1/lnsd/lgtws'

LNS_DATA = [
    {"version":"1.0", "euid":"b827:ebff:fee7:7681","uri":"ws://0.0.0.0:6038/router-"},
    {"version":"1.0", "euid":"b827:ebff:fee7:7682","uri":"ws://0.0.0.0:6038/router-"}
    ]
LGTW_DATA = [
    {"version":"1.0", "euid":"b827:ebff:fee7:7681","lgtw_euid":"::1"},
    {"version":"1.0", "euid":"b827:ebff:fee7:7682","lgtw_euid":"::2"},
    ]

def get_data(uri):
    b = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL,uri)
    c.setopt(c.WRITEDATA, b)
    # For older PycURL versions:
    #c.setopt(c.WRITEFUNCTION, buffer.write)
    c.perform()
    c.close()

    body = b.getvalue()
    # Body is a string on Python 2 and a byte string on Python 3.
    # If we know the encoding, we can always decode the body and
    # end up with a Unicode string.
    print(body.decode('iso-8859-1'))
    b.close

def delete_data(uri):
    b = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, uri)
    c.setopt(c.WRITEDATA, b)
    # For older PycURL versions:
    #c.setopt(c.WRITEFUNCTION, buffer.write)
    c.setopt(pycurl.USERNAME, USERNAME)
    c.setopt(pycurl.PASSWORD, PASSWORD)
    #c.setopt(pycurl.VERBOSE, True)
    c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
    c.perform()
    c.close()

    body = b.getvalue()
    # Body is a string on Python 2 and a byte string on Python 3.
    # If we know the encoding, we can always decode the body and
    # end up with a Unicode string.
    print(body.decode('iso-8859-1'))
    b.close

def post_data(uri, data):
    b = BytesIO()
    c = pycurl.Curl()
    # c.setopt(pycurl.CAINFO, certifi.where())
    c.setopt(c.URL, uri)
    c.setopt(c.WRITEDATA, b)
    # For older PycURL versions:
    #c.setopt(c.WRITEFUNCTION, buffer.write)
    c.setopt(pycurl.USERNAME, USERNAME)
    c.setopt(pycurl.PASSWORD, PASSWORD)
    c.setopt(pycurl.POST, 1)
    # c.setopt(pycurl.CUSTOMREQUEST, "POST")
	c.setopt(pycurl.HTTPHEADER,['Content-Type: application/json'])
    c.setopt(pycurl.POSTFIELDS, json.dumps(data))
    # c.setopt(pycurl.VERBOSE, True)
	# c.setopt(pycurl.TIMEOUT, 10)
    # c.setopt(pycurl.COOKIEFILE, cookie)
	# c.setopt(pycurl.COOKIEJAR, cookie)
    # c.setopt(pycurl.USERAGENT, "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)")
    # c.setopt(pycurl.FOLLOWLOCATION, 1)
    # c.setopt(pycurl.MAXREDIRS, 5)
    c.perform()
    c.close()

    body = b.getvalue()
    # Body is a string on Python 2 and a byte string on Python 3.
    # If we know the encoding, we can always decode the body and
    # end up with a Unicode string.
    print(body.decode('iso-8859-1'))
    b.close
    
delete_data(URI_LNSS)
delete_data(URI_LGTWS)

for data in LNS_DATA:
    post_data(URI_LNSS, data)
    
for data in LGTW_DATA:
    post_data(URI_LGTWS, data)
    
get_data(URI_LNSS)
get_data(URI_LGTWS)
