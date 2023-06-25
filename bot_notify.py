#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   hzsft-notify.py --- Event notify
#
#   Copyright (C) 2020, schspa, all rights reserved.
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
import json
import requests
import click
import importlib
import keyring

class WxBot:
    def __init__(self, name, apikey):
        self.name = name
        self.apikey = apikey
        pass

    def send_notify(self, msg, run=True):
        click.echo("send notify to %s run: %s" % (self.name, run))
        # data to be sent to api
        data = {
            'msgtype' : 'markdown',
            "markdown": {
                'content': msg,
                'mentioned_list' :["@all"]
            }
        }
        print(msg)
        if not run:
            return

        server = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=" + \
            self.apikey
        r = requests.post(url = server, data = json.dumps(data),
                          headers = {'Content-Type': 'application/json'})
        click.echo("Notify weixin server, status: {}".format(r.status_code))
        return
    pass

class FsBot:
    def __init__(self, name, apikey):
        self.name = name
        self.apikey = apikey
        pass

    def send_notify(self, title, msg, run=True):
        click.echo("send notify to %s run: %s" % (self.name, run))
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

        print(msg)
        if not run:
            return

        server = "https://open.feishu.cn/open-apis/bot/v2/hook/" + \
            self.apikey
        r = requests.post(url = server, data = json.dumps(data),
                          headers = {'Content-Type': 'application/json'})
        click.echo("Notify feishu server, status: {}".format(r.status_code))
        return

NotifyBots = [FsBot, WxBot]

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

def notify_robot(bottype, botname, secret = None, title = 'Title', message = 'Message', run = True):
    """send notify to chat robot"""

    if len(bottype) != len(botname):
        click.secho("bottype option's number must equal to botname's number");
        exit(-1)

    for (btype, bname) in list(map(lambda x, y: [x, y], bottype, botname)):
        click.secho("Send to %s with %s\n" % (bname, btype))
        _class = str_to_class(__name__, btype)
        pwkey = btype + '_' + bname
        if secret is None:
            secret = keyring.get_password('BotNotify', pwkey)
        if secret is None:
            import getpass
            secret = getpass.getpass('Please input the secret key for bot %s\n' % (pwkey))
            keyring.set_password('BotNotify', pwkey, secret)
            click.secho('Secret for bot %s saved to keyring' % (pwkey), bg='black', fg='green')

        bot = _class(bname, secret)
        bot.send_notify(title, message, run)

@click.command()
@click.option('--bottype', multiple=True,
              type=click.Choice(list(map(lambda x: x.__name__, NotifyBots)), case_sensitive=False),
              default = [NotifyBots[0].__name__])
@click.option('--botname', multiple=True, default=['default'], help = 'if not specified, use default as name')
@click.option('-s', '--secret', default=None, help = 'if not specified, will try to get it from keyring/input')
@click.option('-t', '--title', default="消息同步")
@click.option('-m', '--message', default="Test notify message")
@click.option('--run/--try-run', default=True)
def notify_robot_cli(bottype, botname, secret, title, message, run):
    notify_robot(bottype, botname, secret, title, message, run)
    return

if __name__ == '__main__':
    notify_robot_cli()
