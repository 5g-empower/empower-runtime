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

"""RYU Connector."""

import json
import http.client

from empower.core.jsonserializer import EmpowerEncoder
from empower.datatypes.etheraddress import EtherAddress

import empower.logger
LOG = empower.logger.get_logger()

# TODO: This should be automatically built. Update if topology is different.
CPPS = {
        EtherAddress("00:00:24:d1:61:ed"): {
            EtherAddress("00:0D:B9:2F:56:58"): 2,
            EtherAddress("00:0D:B9:2F:56:5c"): 3,
            EtherAddress("00:0D:B9:2F:56:64"): 1,
        },
        EtherAddress("00:00:24:D1:83:55"): {
            EtherAddress("00:0D:B9:2F:56:58"): 2,
            EtherAddress("00:0D:B9:2F:56:5c"): 2,
            EtherAddress("00:0D:B9:2F:56:64"): 3,
        },
    }


class RyuFlowEntry():

    def __init__(self, server="localhost", port=8080):

        self.server = server
        self.port = port

    def run(self, cmd, data):

        body = json.dumps(data, indent=4, cls=EmpowerEncoder)

        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }

        try:

            conn = http.client.HTTPConnection(self.server, self.port)
            conn.request("POST", "/stats/flowentry/%s" % cmd, body, headers)
            response = conn.getresponse()

            ret = (response.status, response.reason, response.read())
            LOG.info("Result: %u %s" % (ret[0], ret[1]))
            conn.close()

        except:

            LOG.error("Connection refused.")

    def add(self, dpid, match, actions):

        data = {
            "dpid": dpid.to_int(),
            "match": match,
            "actions": actions
         }

        self.run("add", data)

    def delete(self, dpid, match, actions):

        data = {
            "dpid": dpid.to_int(),
            "match": match,
            "actions": actions
         }

        self.run("delete", data)

    def add_station_flows(self, lvap_addr, dpid, port_id):

        # add flow entry on wtp
        match = {
            "dl_dst": lvap_addr
        }

        actions = [
            {
                "type": "OUTPUT",
                "port": port_id
            }
        ]

        LOG.info("DPID %s: LVAP %s is on port %u" % (dpid, lvap_addr, port_id))
        self.add(dpid=dpid, match=match, actions=actions)

        # add flow entry on all cpps
        for cpp in CPPS:

            match = {
                "dl_dst": lvap_addr
            }

            actions = [
                {
                    "type": "OUTPUT",
                    "port": CPPS[cpp][dpid]
                }
            ]

            LOG.info("DPID %s: LVAP %s is on port %u" %
                     (cpp, lvap_addr, CPPS[cpp][dpid]))

            self.add(dpid=cpp, match=match, actions=actions)

    def remove_station_flows(self, lvap_addr, dpid):

        # remove flow entry from old wtp
        match = {
            "dl_dst": lvap_addr
        }

        LOG.info("DPID %s: LVAP %s remove" % (dpid, lvap_addr))
        self.delete(dpid=dpid, match=match, actions=[])

        # remove flow entry from all cpps
        for cpp in CPPS:

            match = {
                "dl_dst": lvap_addr
            }

            LOG.info("DPID %s: LVAP %s remove" % (cpp, lvap_addr))
            self.delete(dpid=cpp, match=match, actions=[])
