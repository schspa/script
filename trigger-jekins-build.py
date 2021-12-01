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
import json
import time
import getpass
import sys
import click
import requests


BUILD_PROGRESSIVETEXT_OUTPUT = '%(folder_url)sjob/%(short_name)s/%(number)s/logText/progressiveText?start='

def dump_build_console_output(self, name, number):
    '''Get build console text.
    :param name: Job name, ``str``
    :param number: Build number, ``str`` (also accepts ``int``)
    :returns: Build console output,  ``str``
    '''
    folder_url, short_name = self._get_job_folder(name)
    need_more = True
    start = '0'
    while need_more:
        try:
            url_base = BUILD_PROGRESSIVETEXT_OUTPUT + start
            response = self.jenkins_request(requests.Request(
                'GET', self._build_url(url_base, locals())
            ))
            if response:
                if 'X-More-Data' not in response.headers:
                    need_more = False
                    click.echo(response.text)
                else:
                    start = response.headers['X-Text-Size']
                    click.echo(response.text, nl = False)
                    time.sleep(1);
            else:
                raise jenkins.JenkinsException('job[%s] number[%s] does not exist'
                                   % (name, number))
        except (jenkins.req_exc.HTTPError, jenkins.NotFoundException):
            raise jenkins.JenkinsException('job[%s] number[%s] does not exist'
                                           % (name, number))

def create_job(server, buildname, json_file, case = None, verbose = False):
    # https://stackoverflow.com/questions/53355389/python-2-3-compatibility-issue-with-exception
    try:
        json_parse_exception = json.decoder.JSONDecodeError
    except AttributeError:  # Python 2
        json_parse_exception = ValueError
        pass

    try:
        params = json.loads(json_file)
    except json_parse_exception:
        with open(json_file) as f:
            params = json.load(f)
    if case is not None:
        params['JSON_FILE'] = case
    number=server.build_job(buildname, params)

    bn=None
    while True:
        info=server.get_queue_item(number)
        try:
            bn = info['executable']['number']
            if verbose:
                click.echo(json.dumps(info, indent=4, sort_keys=True))
                pass
            click.secho('Get jekins build at: %s' % (info['executable']['url']), bg='black', fg='green')
            return bn
        except KeyError as e:
            time.sleep(5)
            click.secho('Wait jobs create')
            pass
        pass
    pass

def wait_job_status(server, buildname, bn, verbose = False):
    is_building = True
    jinfo={}
    while is_building:
        jinfo=server.get_build_info(buildname, bn)
        is_building = jinfo['building']
        if is_building:
            time.sleep(5)
            click.echo("Waiting for build complete")
            pass

    if verbose:
        click.echo(json.dumps(jinfo, indent=4, sort_keys=True))

    click.secho('Jekins build url: %s' % (jinfo['url']),
                bg='black',
                fg='green' if jinfo['result'] == 'SUCCESS' else 'red')
    click.secho('Jekins Report url: %s' % (jinfo['url'] + 'HTMLReport'),
                bg='black',
                fg='green' if jinfo['result'] == 'SUCCESS' else 'red')
    return 0 if jinfo['result'] == 'SUCCESS' else -1;

@click.command()
@click.option('-r', '--url', default='http://ci.athion.net')
@click.option('-u', '--username', default=None)
@click.option('-p', '--password', default=None)
@click.option('-j', '--json_file')
@click.option('-c', '--case', default=None)
@click.option('-b', '--buildname')
@click.option('--verbose', is_flag=True)
def trigger_jekins_build(url, buildname, username, password, json_file, case, verbose):
    """Create a new jekins build and wait for build exit with status"""

    if username is None:
        username = getpass.getuser()

    if password is None:
        password = getpass.getpass()
    elif password == "-":
        password = sys.stdin.read().strip()
        pass

    server = jenkins.Jenkins(url, username=username, password=password)
    bn = create_job(server, buildname, json_file, case, verbose)
    dump_build_console_output(server, buildname, bn)
    ret = wait_job_status(server, buildname, bn, verbose)
    sys.exit(ret)

if __name__ == '__main__':
    trigger_jekins_build()
