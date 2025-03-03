#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   sync-to-gitlab.py --- Sync project to gitlab
#
#   Copyright (C) 2021, Schspa, all rights reserved.
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
import subprocess
import click

from project_create import create_gitlab_project

@click.command()
@click.option('--verbose', is_flag=True, help="Will print verbose messages.")
@click.option('--rootproject', default=1, help='root project id')
@click.option('--server', default='https://gitlab.com/', help='gitlab server url')
@click.option('--token', default=None, help='gitlab server access token')
@click.argument('path')
def cli(verbose, rootproject, server, token, path):
    #ssh_url = create_gitlab_project(server, token, path, rootproject, verbose)
    #print("repository: %s" %(ssh_url))
    output=subprocess.check_output("repo list", shell=True, cwd=path).decode('utf-8')
    projects = output.splitlines()
    for project in projects:
        repository_path, repository_url = project.split(" : ")
        if repository_url == 'platform/build':
            repository_url = 'platform/build/make'
            pass
        elif repository_url == 'device/common':
            repository_url = 'device/common/comm'
            pass
        elif repository_url == 'miui/config-overlay':
            continue
        elif repository_url == 'platform/prebuilts/go/linux-x86':
            continue
        repository_path = os.path.join(path, repository_path)
        print("Creating repository %s" % (repository_url))
        try:
            ssh_url = create_gitlab_project(server, token, repository_url, rootproject, verbose)
        except Exception:
            continue

        try:
            print('Push %s to %s' % (repository_path, ssh_url))
            output=subprocess.check_output(
                "git push -u %s --tags" % (ssh_url),
                shell=True, cwd=repository_path).decode('utf-8')
        except subprocess.CalledProcessError:
            pass
        output=subprocess.check_output("git branch -a", shell=True, cwd=repository_path).decode('utf-8')
        # git push -f -u xxx.git refs/remotes/origin/xxx:refs/heads/xxx
        branches = output.splitlines()
        for branch in branches:
            try:
                localrefs, remoterefs = branch.split(" -> ")
                localrefs = localrefs.strip()
                remoterefs = remoterefs.strip()
                print("local: %s remote: %s" % (localrefs, remoterefs))
                branch_name = remoterefs.split('/')[1]
                print('cwd = %s' % (repository_path))
                print("git push -u %s refs/%s:refs/heads/%s" % (ssh_url, localrefs, branch_name))
                try:
                    output=subprocess.check_output(
                        "git push -u %s refs/%s:refs/heads/%s" % (ssh_url, localrefs, branch_name)
                        ,shell=True,
                        cwd=repository_path).decode('utf-8')
                except subprocess.CalledProcessError:
                    pass
            except ValueError:
                pass
    pass

if __name__ == '__main__':
    cli()
