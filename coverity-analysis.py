#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   coverity-analysis.py --- coverity-analysis
#
#   Copyright (C) 2022, Schspa Shi, all rights reserved.
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

import json
import time
import getpass
import sys
import click
import requests
import subprocess
import tempfile
import logging
from pprint import pprint

class CovSessionError(BaseException):
    category = 'Coverrity Session Error'


class CovSession:
    def __init__(self, url, user, password):
        self.base_url = url
        self.auth = (user, password)

    def request(self, url, params = {}):
        r = requests.get(url = f'{self.base_url}/{url}',
                         params=params,
                         auth=self.auth)
        if not r.ok:
            raise CovSessionError(f'request faile with status {r.status_code}')

        logging.debug(r.text)

        data = json.loads(r.text)

        logging.debug(json.dumps(data, indent = 4))

        return data

    def get_defects(self, snapshot):
        return self.request(f'reports/snapshots/{snapshot}/details.json')

    def get_snapshotExpression(self, projectid, snapshot):
        return self.request('reports/defects.json', params={
                         'projectId' : projectid,
                         'snapshotExpression' : snapshot
                     })


@click.command()
@click.option('-r', '--url', default='https://coverity.com')
@click.option('--user', default=None)
@click.option('--password', default=None)
@click.option('-p', '--projectid', type = int, default=1)
@click.option('-s', '--snapshot', type = int, default=1)
@click.option('-v', '--verbose', is_flag=True)
def get_coverity_summary(url, user, password, projectid, snapshot, verbose):
    '''Show the details for coverity snapshot'''

    logging.basicConfig(level=logging.DEBUG if verbose else logging.ERROR)

    covs = CovSession(url, user, password)
    cov_defects = covs.get_defects(snapshot)
    cov_snapshot_exp = covs.get_snapshotExpression(projectid, snapshot)

    click.secho('Coverity totalDefectCount: {}'.format(cov_defects['snapshotDetails']['totalDefectCount']))
    click.secho('Coverity Report url: {}'.format(url + cov_snapshot_exp['url']), bg='black', fg='green')

    sys.exit(0)

if __name__ == '__main__':
    get_coverity_summary()
