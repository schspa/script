#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   log-monitor.py<script> --- Description
#
#   Copyright (C) 2024, Schspa, all rights reserved.
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
import sys
import time
import json
import requests
import click
import importlib
import traceback
import logging
import logging.handlers

class FsBot:
    def __init__(self, name, apikey):
        self.name = name
        self.apikey = apikey
        pass

    def send_notify(self, title, msg, run=True):
        click.echo("send notify to %s msg: %s run: %s" % (self.name, msg, run))
        # data to be sent to api
        data = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": msg
                                }
                            ]
                        ]
                    }
                }
            }
        }

        from pprint import pprint
        pprint(data)
        if not run:
            return

        server = "https://open.feishu.cn/open-apis/bot/v2/hook/" + \
            self.apikey
        try:

            print('server: %s' % (server))
            r = requests.post(url = server, data = json.dumps(data),
                          headers = {'Content-Type': 'application/json'})
            click.echo("Notify feishu server, status: {}".format(r.status_code))
            return True
        except requests.exceptions.ConnectionError as e:
            click.echo("Notify feishu server failed".format(r.status_code))
            traceback.print_exception(*sys.exc_info())

        return False

NotifyBots = [FsBot]

def str_to_class(module_name, class_name):
    """Return a class instance from a string reference"""
    try:
        module_ = importlib.import_module(module_name)
        try:
            class_ = getattr(module_, class_name)
        except AttributeError:
            logging.error('Class does not exist')
    except ImportError:
        logging.error('Module does not exist')
    return class_ or None

def notify_robot(bottype, secret = None, title = 'Title', message = 'Message', run = True):
    """send notify to chat robot"""

    _class = str_to_class(__name__, bottype)

    bot = _class(bottype, secret)
    return bot.send_notify(title, message, run)


def send_email(subject, secret, logs):
        notify_robot('FsBot', secret, subject, logs)
        print("Get error")

def monitor_log(log_file):
    with open(log_file, 'r') as f:
        f.seek(0, 2)  # Go to the end of the file
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            print(line)
            if "suspend" in line:
                send_email("Error in log file", line)

if __name__ == "__main__":
    log_file = sys.argv[1]
    bot_secret = sys.argv[2]
    key_words = sys.argv[3]
    monitor_log(log_file)
