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
import os
import json
import time
import getpass
import sys
import click
import requests
import subprocess
import tempfile
import shlex
from urllib.parse import urlparse
from pprint import pprint


def arrange_patchs(patches):
    for project, pi in patches.items():
        click.secho('arrange for %s' % (project), bg='black', fg='white')
        out = []
        found = True
        done = False

        patchs = pi['patches']
        while not done:
            found = False
            for i in range(len(patchs)):
                if len(out) == 0:
                    out.append(patchs[i])
                    patchs.pop(i)
                    found = True
                    break;
                for j in range(len(out)):
                    pprint(out[j])
                    pprint(patchs[i])
                    if out[j]['rev'] == patchs[i]['parent']:
                        out.insert(j + 1, patchs[i])
                        patchs.pop(i)
                        found = True
                        break
                    if out[j]['parent'] == patchs[i]['rev']:
                        out.insert(j, patchs[i])
                        patchs.pop(i)
                        found = True
                        break

            if not found:
                done = True
                break

        pi['patches'] = out

def get_directory_path_from_url(url):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')[1:]  # Split path and remove the leading empty segment

    # Assuming the structure is always /c/<directory_path>/+/<numbers>
    # and you want to retrieve only the <directory_path> part:
    if len(path_segments) > 1 and path_segments[0] == 'c':
        directory_path = '/'.join(path_segments[1:-2])  # Exclude the '+/numbers' segment
        return directory_path
    return None  # Return None or appropriate value if URL doesn't match the expected pattern

# url = "https://gerrit.xxx.cc:8443/c/cs/aa/bb/+/15198"
# print(get_directory_path_from_url(url))

def repo_info_to_dict(project):
    # Execute the 'repo info' command and capture the output
    result = subprocess.run(['repo', 'info', project], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check if the command was successful
    if result.returncode != 0:
        print("Error running 'repo info':", result.stderr)
        return None

    # Parse the output to create a dictionary
    repo_info_dict = {}
    for line in result.stdout.split('\n'):
        # Split each line into a key-value pair
        parts = line.split(': ', 1)
        if len(parts) == 2:
            key, value = parts
            repo_info_dict[key.strip()] = value.strip()

    return repo_info_dict

@click.command()
@click.option('-r', '--url', default='gerrit.test.com')
@click.option('-p', '--port', type=int, default=29418)
@click.option('-u', '--user', default='admin')
@click.option('-t', '--topic', default='topic')
@click.option('-v', '--verbose', is_flag=True)
@click.option('-n', '--not_apply', is_flag=True, default=False)
def get_gerrit_changes(url, port, user, topic, verbose, not_apply):
    """Create a new gitlab build and wait for build exit with status"""
    commands = shlex.split('ssh -p {:d} {:s}@{:s} gerrit query --format=JSON --current-patch-set status:open topic:{:s}'.format(port, user, url, topic))
    output = subprocess.check_output(
        commands, stderr=subprocess.STDOUT).decode("utf-8")
    with open(os.path.join(os.getcwd(), 'gerrit-query-out.txt'), 'w') as f:
        f.write(output)

    # output = ''
    # with open(os.path.join(os.path.expanduser('~/gerrit-query-out.txt')), 'r') as f:
    #     output = f.read()

    patchs = {}
    for item in output.splitlines():
        res = json.loads(item)
        if verbose:
            print(json.dumps(res, sort_keys=True, indent=4))
            pass
        if 'type' in res.keys():
            continue

        pprint(res)
        project = res['project']
        subject = res['subject']
        ref = res['currentPatchSet']['ref']
        rev = res['currentPatchSet']['revision']
        parent = res['currentPatchSet']['parents'][0]
        current_patch = {
            'subject': subject,
            'ref': ref,
            'rev': rev,
            'parent': parent,
            'project': parent,
            'next': None
        }
        if project not in patchs.keys():
            # first patchset in current project
            patchs[project] = {}
            patchs[project]['patches'] = [current_patch]
        else:
            patchs[project]['patches'].append(current_patch)

        patchs[project]['branch'] = res['branch']
        patchs[project]['url'] = res['url']
        patchs[project]['rpath'] = get_directory_path_from_url(res['url'])

        project_dir = project.replace('cs/self/', '')
        click.secho('Project: %s' % (project), bg='black', fg='white')
        click.secho('Subject: %s' % (subject), bg='black', fg='white')
        click.secho('Ref: %s' % (ref), bg='black', fg='white')
        click.secho('Parent: %s' % (parent), bg='black', fg='white')
        click.secho('Revision: %s' % (rev), bg='black', fg='white')
        click.secho('---------------------------------', bg='black', fg='white')
        if not_apply:
            continue

    arrange_patchs(patchs)
    pprint(patchs)

    project_paths = subprocess.check_output(
        shlex.split('repo list -p'), stderr=subprocess.STDOUT).decode("utf-8")
    for project in project_paths.splitlines():
        click.secho('project: %s' % (project), bg='black', fg='white')
        ri = repo_info_to_dict(project)
        if ri is None:
            continue
        # pprint(ri)
        p_mnt = ri['Mount path']
        repoinfo = subprocess.check_output(
            shlex.split('git config -l'.format(project)),
            cwd=p_mnt,
            stderr=subprocess.STDOUT).decode("utf-8")
        for project, pi in patchs.items():
            if pi['rpath'] not in repoinfo:
                continue
            for patch in pi['patches']:
                ref = patch['ref']
                click.secho('applying patch: %s' % (patch['subject']), bg='black', fg='white')
                commands = shlex.split('git fetch ssh://{:s}@{:s}:{:d}/{:s} {:s}'.format(user, url, port, project, ref))
                output = subprocess.check_output(
                    commands,
                    cwd=p_mnt,
                    stderr=subprocess.STDOUT).decode("utf-8")
                commands = shlex.split('git cherry-pick FETCH_HEAD')
                output = subprocess.check_output(
                    commands,
                    cwd=p_mnt,
                    stderr=subprocess.STDOUT).decode("utf-8")

    sys.exit(0)

if __name__ == '__main__':
    get_gerrit_changes()
