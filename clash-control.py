#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   clashctrl.py --- Clash control
#
#   Copyright (C) 2023, Schspa, all rights reserved.
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import requests
import json
import logging
from termcolor import colored, cprint

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token

        return r

class ClashControl():

    def __init__(self, url, token):
        self.auth = BearerAuth(args.token)
        self.url = url
        self.token = token
        self.colors = {
            'debug': 'light_cyan',
            'info': 'white',
            'warn': 'light_red',
            'error' : 'red'
        }
        logging.debug(f"controller url: {self.url} token: {self.token}")

    def refresh_config(self, config):
        with open(args.config, "r") as f:
            myobj = {'payload': f.read() }
            # print(json.dumps(myobj, indent=4))

        x = requests.put(self.url + '/configs', auth=self.auth,
                      headers={"Content-Type" : "application/json"},
                      data=json.dumps(myobj, indent=4))

        if not x.ok:
            exit(-1);


    def log(self):
        try:
            r = requests.get(self.url + '/logs', headers = {'level' : "debug"}, auth = self.auth, stream=True)
            for line in r.iter_lines():
                if not line:
                    return
                li = json.loads(line)

                cprint('{:<6s} {:s}'.format(li['type'] + ':', li['payload']), self.colors[li['type']], "on_black")
        except KeyboardInterrupt:
            return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, help="clash control command", choices=['reload', 'log'])
    parser.add_argument("--config", type=str, help="clash config yaml path")
    parser.add_argument("--url", type=str, help="clash controller url", default='http://localhost:9090')
    parser.add_argument("--token", type=str, help="clash controller token", default='123456')
    parser.add_argument("--verbose", help="Enable verbose debug log", action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.WARNING)

    clashc = ClashControl(args.url, args.token)

    if args.command == 'reload':
        clashc.refresh_config(args.config)

    if args.command == 'log':
        clashc.log()
