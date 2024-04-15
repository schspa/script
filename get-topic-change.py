#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   get-topic-change.py --- Description
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
import json
import time
import getpass
import sys
import click
import requests
import subprocess
import tempfile
import shlex


@click.command()
@click.option('-r', '--url', default='gerrit.test.com')
@click.option('-p', '--port', type=int, default=8443)
@click.option('-u', '--user', default='admin')
@click.option('-t', '--topic', default='topic')
@click.option('-v', '--verbose', is_flag=True)
def get_gerrit_changes(url, port, user, topic, verbose):
    """Create a new gitlab build and wait for build exit with status"""
    commands = shlex.split('ssh -p {:d} {:s}@{:s} gerrit query --format=JSON --current-patch-set status:open topic:{:s}'.format(port, user, url, topic))
    output = subprocess.check_output(
        commands, stderr=subprocess.STDOUT).decode("utf-8")
    for item in output.splitlines():
        res = json.loads(item)
        if verbose:
            print(json.dumps(res, sort_keys=True, indent=4))
            pass
        if 'type' in res.keys():
            continue

        project = res['project']
        subject = res['subject']

        project_dir = project.replace('cs/self/', '')
        ref = res['currentPatchSet']['ref']
        click.secho('Project: %s' % (project), bg='black', fg='white')
        click.secho('Subject: %s' % (subject), bg='black', fg='white')
        click.secho('Ref: %s' % (ref), bg='black', fg='white')
        commands = shlex.split('git fetch ssh://{:s}@{:s}:{:d}/{:s} {:s}'.format(user, url, port, project, ref))
        output = subprocess.check_output(
            commands,
            cwd=project_dir,
            stderr=subprocess.STDOUT).decode("utf-8")
        print(output)
        commands = shlex.split('git reset --hard FETCH_HEAD')
        output = subprocess.check_output(
            commands,
            cwd=project_dir,
            stderr=subprocess.STDOUT).decode("utf-8")
        print(output)

    sys.exit(0)

if __name__ == '__main__':
    get_gerrit_changes()
