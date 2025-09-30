#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   get-debian-version.py --- Description
#
#   Copyright (C) 2025, Schspa, all rights reserved.
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


import sys
import re
import requests
import click
from loguru import logger
from datetime import datetime
from configparser import ConfigParser


def extract_version_regex(text):
    # 匹配 Version: 后面的版本号
    pattern = r'Version:\s*([\d.]+)'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None

def convert_date_to_utc_timestamp(text):
    # 使用正则表达式提取日期行
    date_pattern = r'Date:\s*(.+?)\s*UTC'
    match = re.search(date_pattern, text)

    if match:
        date_str = match.group(1).strip()

        # 解析日期字符串
        # 注意：格式必须与输入严格匹配
        dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S')

        # 由于输入已经是 UTC，直接转换为时间戳
        utc_timestamp = dt.timestamp()

        return utc_timestamp

    return None

def get_debian_version(dist):
    url = f'http://ftp.cn.debian.org/debian/dists/{dist}/Release'
    ## header is needed, on some environment, it will return 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    logger.debug(f"Request: {url}")
    response = requests.get(url, allow_redirects=True, headers = headers)
    if not response.ok:
        print(f"request failed with status {response.status_code}")

    debian_version = extract_version_regex(response.text)
    debian_date = convert_date_to_utc_timestamp(response.text)
    logger.info(f'get debian_version: { debian_version } date: {debian_date}')
    return debian_version, debian_date

def update_debian_version(app_id, table, record, token, version, date):
    url = f'https://base-api.feishu.cn/open-apis/bitable/v1/apps/{app_id}/tables/{table}/records/{record}?ignore_consistency_check=true'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
    }
    data = {
          "fields": {
                  "版本号": version,
                  "日期": int(date * 1000)
          }
    }

    response = requests.put(url, json=data, headers=headers)
    logger.debug(f"状态码: {response.status_code}")
    logger.debug(f"response: { response.text }")
    if response.ok:
        logger.info("资源更新成功")
        logger.debug(response.json())

DEFAULT_CFG = '/etc/debian_update_notify.ini'

def configure(ctx, param, filename):
    cfg = ConfigParser()
    print(filename)
    cfg.read(filename)
    try:
        options = dict(cfg['options'])
    except KeyError:
        options = {}
    ctx.default_map = options

@click.command()
@click.option('-a', '--app_id', default=None)
@click.option('-t', '--table', default=None)
@click.option('-r', '--record', default=None)
@click.option('-k', '--token', default=None)
@click.option('-d', '--dist', default='bookworm')
@click.option('--verbose', is_flag=True)
@click.option(
    '-c', '--config',
    type         = click.Path(dir_okay=False),
    default      = DEFAULT_CFG,
    callback     = configure,
    is_eager     = True,
    expose_value = False,
    help         = 'Read option defaults from the specified INI file',
    show_default = True,
)
def update_debian_version_to_bitable(app_id, table, record, token, dist, verbose):
    """Get newest debian version and update to feishu bitable"""
    handler = {"sink": sys.stderr, "level": "INFO"}
    if verbose:
        handler = {"sink": sys.stderr, "level": "DEBUG"}
    logger.configure(handlers=[handler])

    debian_version, debian_date = get_debian_version(dist)
    update_debian_version(app_id, table, record, token, debian_version, debian_date)

if __name__ == '__main__':
    update_debian_version_to_bitable()
