#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   build-req.py --- Description
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

# refs: https://python-jenkins.readthedocs.io/en/latest/examples.html#example-3-working-with-jenkins-jobs

import jenkins
import getpass
import sys
import click

def get_build_output(server, build_name, build_number):
    logs = server.get_build_console_output(build_name, build_number)
    return logs

@click.command()
@click.option('-r', '--url', default='http://ci.athion.net')
@click.option('-u', '--username', default=None)
@click.option('-p', '--password', default=None)
@click.option('-b', '--buildname')
@click.option('-n', '--buildnumber', default=None, type=int)
@click.option('--verbose', is_flag=True)
def get_jekins_log(url, username, password, buildname, buildnumber, verbose):
    """Create a new jekins build and wait for build exit with status"""

    if username is None:
        username = getpass.getuser()

    if password is None:
        password = getpass.getpass()
    elif password == "-":
        password = sys.stdin.read().strip()
        pass

    server = jenkins.Jenkins(url, username=username, password=password)
    logs = get_build_output(server, buildname, buildnumber)
    print(logs)
    sys.exit(0)

if __name__ == '__main__':
    get_jekins_log()
