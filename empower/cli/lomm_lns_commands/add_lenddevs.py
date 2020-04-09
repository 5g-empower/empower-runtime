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

"""Add new lEndDevs to the LNS database."""

import argparse
import json

from empower.cli import command


KEYS = dict(dev_addr="devAddr",
            net_id="netID", lversion="lVersion",
            desc="desc", tags="tags",
            owner="owner", join_eui="joinEUI",
            activation="activation", dev_class="devClass",
            lgtws_range="lGtwsRange", label="label",
            app_key="appKey", nwk_key="nwkKey",
            app_s_key="appSKey", nwk_s_enc_key="nwkSEncKey",
            f_nwk_s_int_key="fNnwkSIntKey", s_nwk_s_int_key="sNnwkSIntKey",
            location="location",
            fcnt_checks="fCntChecks",
            fcnt_size="fCntSize",
            payloadFormat="payloadFormat")


def pa_cmd(args, cmd):
    """Add lenddevs parser method.

    usage: empower-ctl.py add-lenddevs <options>

    optional arguments:
      -h, --help            show this help message and exit

    required named arguments:
      -e DEVEUI, --devEUI DEVEUI
                            devEUI euid
      -j JSON_FILE, --json JSON_FILE
                            json file
    """

    usage = "%s <options>" % command.USAGE.format(cmd)
    desc = command.DESCS[cmd]

    parser = argparse.ArgumentParser(usage=usage, description=desc)

    group = parser.add_argument_group('required mutually exclusive arguments')

    required = group.add_mutually_exclusive_group(required=True)

    required.add_argument(
        "-e", "--devEUI", help="devEUI euid",
        type=str, dest="devEUI")

    required.add_argument(
        "-j", "--json", help="json file",
        type=str, dest="json_file")

    (args, leftovers) = parser.parse_known_args(args)

    return args, leftovers


def do_cmd(gargs, args, _):
    """Add a new lenddevs."""

    headers = command.get_headers(gargs)
    url = '/api/v1/lns/lenddevs/'

    if args.json_file:

        with open(args.json_file, 'r') as file:
            lenddevs = json.load(file)

        for lenddev in lenddevs:
            dev_eui = lenddev.get("devEUI")
            if not dev_eui:
                print("devEUI missing, cannot add device")
                return
            request = dict(version="1.0")
            for key, value in KEYS.items():
                if value in lenddev:
                    request[key] = lenddev[value]
            # url = '/api/v1/lns/lenddevs/%s' % devEUI
            try:
                response, _ = command.connect(
                    gargs, ('POST', url + dev_eui), 201, request,
                    headers=headers, exit_on_err=False)
            except Exception as err:
                print(err)
            else:
                location = response.headers['Location']
                tokens = location.split("/")
                dev_eui = tokens[-1]
                print("lEndDev (%s) added to LNS  Database" % dev_eui)
            print()

    else:

        request = {}
        url += args.devEUI
        try:
            response, _ = command.connect(
                gargs, ('POST', url), 201, request,
                headers=headers, exit_on_err=False)
        except Exception as err:
            print(err)
        else:
            location = response.headers['Location']
            tokens = location.split("/")
            dev_eui = tokens[-1]
            print("lEndDev (%s) added to LNS  Database" % dev_eui)
        print()
