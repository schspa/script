#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   cf_ddns.py --- DDNS for cloudflare
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
import sys
import CloudFlare
import time
import click
import requests
import json

from configparser import ConfigParser
from pprint import pprint

file_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(file_path)))

from bot_notify import notify_robot

g_feishu_secret = ""

def notify(message):
    global g_feishu_secret
    if g_feishu_secret is not None:
        notify_robot(['FsBot'], ['default'], title = 'cf_ddns', message = message, secret = g_feishu_secret)
    print(message)

def error_report(message):
    notify(message)
    exit(message)

# https://github.com/cloudflare/python-cloudflare

def my_ip_address():
    """Cloudflare API code - example"""

    # This list is adjustable - plus some v6 enabled services are needed
    # url = 'http://myip.dnsomatic.com'
    ip_test_url = [
        # 'http://myip.dnsomatic.com',
        'http://www.trackip.net/ip',
        'http://myexternalip.com/raw',
        # 'http://www.trackip.net/ip',
        # 'https://api.ipify.org'
    ]
    for url in ip_test_url:
        response = requests.get(url, headers = {
            'accept': 'text/plain',
        })
        if response.ok:
            ip_address = response.text
            break

    if ip_address == '':
        error_report('%s: failed' % (url))

    if ':' in ip_address:
        ip_address_type = 'AAAA'
    else:
        ip_address_type = 'A'

    return ip_address, ip_address_type

def do_dns_update(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type):
    """Cloudflare API code - example"""

    try:
        params = {'name':dns_name, 'match':'all', 'type':ip_address_type}
        dns_records = cf.zones.dns_records.get(zone_id, params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        error_report('/zones/dns_records %s - %d %s - api call failed' % (dns_name, e, e))

    updated = False

    # update the record - unless it's already correct
    for dns_record in dns_records:
        old_ip_address = dns_record['content']
        old_ip_address_type = dns_record['type']
        print(f'Old ip address {old_ip_address}')

        if ip_address_type not in ['A', 'AAAA']:
            # we only deal with A / AAAA records
            continue

        if ip_address_type != old_ip_address_type:
            # only update the correct address type (A or AAAA)
            # we don't see this becuase of the search params above
            print('IGNORED: %s %s ; wrong address family' % (dns_name, old_ip_address))
            continue

        if ip_address == old_ip_address:
            print('UNCHANGED: %s %s' % (dns_name, ip_address))
            updated = True
            continue

        proxied_state = dns_record['proxied']

        # Yes, we need to update this record - we know it's the same address type

        dns_record_id = dns_record['id']
        dns_record = {
            'name':dns_name,
            'type':ip_address_type,
            'content':ip_address,
            'proxied':proxied_state
        }
        try:
            dns_record = cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            error_report('/zones.dns_records.put %s - %d %s - api call failed' % (dns_name, e, e))
        notify('UPDATED: %s %s -> %s' % (dns_name, old_ip_address, ip_address))
        updated = True

    if updated:
        return

    # no exsiting dns record to update - so create dns record
    dns_record = {
        'name':dns_name,
        'type':ip_address_type,
        'content':ip_address
    }
    try:
        dns_record = cf.zones.dns_records.post(zone_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        error_report('/zones.dns_records.post %s - %d %s - api call failed' % (dns_name, e, e))
    notify('CREATED: %s %s' % (dns_name, ip_address))


def cf_update_myip(token, zone_name, domain, ip, debug, feishu_secret):

    global g_feishu_secret
    g_feishu_secret = feishu_secret

    if ip is None:
        ip = my_ip_address()

    if ip is None:
        print("Failed to aws instance ip address")
        error_report(-1)

    notify(f'Got ip address: {ip}')
    cf = CloudFlare.CloudFlare(token = token, debug=debug)

    def get_zone_id(name):
        zones = cf.zones.get()
        for zone in zones:
            if debug:
                print('%s Found zone: %s id: %s' % (name, zone['name'], zone['id']))
            if zone['name'] == name:
                return zone['id']

        return None

    zone_id = get_zone_id(zone_name)
    if zone_id is None:
        print("Failed to get zone_id for %s" % (zone_name))
        return -1;

    do_dns_update(cf, zone_name, zone_id, domain, ip, 'A')


DEFAULT_CFG = '/etc/cf_ddns.ini'

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
@click.option('-t', '--token', default=None)
@click.option('-z', '--zone_name', default=None)
@click.option('-domain', '--domain', default=None)
@click.option('-i', '--ip', default=None)
@click.option('--debug', is_flag=True, default = False)
@click.option('--feishu_secret', default=None, type = str)
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
def cli(**kwargs):
    print(json.dumps(kwargs, sort_keys=True, indent=4))
    cf_update_myip(**kwargs)

if __name__ == '__main__':
    cli()
