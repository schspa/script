#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   trigger-gitlab-build.py --- gitlab jobs runner
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


@click.command()
@click.option('-r', '--url', default='https://gitlab.com')
@click.option('-p', '--project', type = int, default='1')
@click.option('--ref', default='master')
@click.option('--trigger_token', default=None)
@click.option('--private_token', default=None)
@click.option('-j', '--var_json')
@click.option('--jobname', default="build")
@click.option('--output', default=None)
@click.option('--pipeline', type=int, default=None)
@click.option('--verbose', is_flag=True)
def trigger_gitlab_build(url, project, ref, trigger_token, private_token, var_json, jobname, output, pipeline, verbose):
    """Create a new gitlab build and wait for build exit with status"""
    if pipeline is None:
        vardata = {
            "token": trigger_token,
            "ref" : ref
        }
        if var_json is not None:
            vardata = {**vardata, **json.loads(var_json)}
            pass

        r = requests.post(url = "{:s}/api/v4/projects/{:d}/trigger/pipeline".format(
        url, project), data = vardata)
        res = json.loads(r.text)
        if verbose:
            print(json.dumps(res, sort_keys=True, indent=4))
            pass

        click.secho('Get gitlab pipeline id: %d, url: %s' % (res['id'], res['web_url']),
                    bg='black',
                    fg='green')
        pipeline = res['id']

    download_header = {
        "PRIVATE-TOKEN": private_token
    }
    pstatus = None
    pipeline_status = None
    while pstatus not in ["success", "failed", "canceled", "skipped", "manual", "scheduled"]:
        r = requests.get(url = "{:s}/api/v4/projects/{:d}/pipelines/{:d}".format(
            url, project, pipeline), headers = download_header)
        pipeline_status = json.loads(r.text)
        if verbose:
            print(json.dumps(pipeline_status, sort_keys=True, indent=4))
            pass
        pstatus = pipeline_status['status']
        time.sleep(5)
        click.echo("Waiting for pipeline complete, status: {:s}".format(pipeline_status['status']))
        pass

    if pstatus != 'success':
        click.secho('Pipeline: %s failed with status %s' % (pipeline_status['web_url'] + pstatus),
                bg='black',
                fg='red')
        sys.exit(-1);

    r = requests.get(url = "{:s}/api/v4/projects/{:d}/pipelines/{:d}/jobs".format(
        url, project, pipeline), headers = download_header)
    if verbose:
        print(json.dumps(json.loads(r.text), sort_keys=True, indent=4))
        pass

    res = json.loads(r.text)
    click.echo('Commit shot id %s' % (res[0]['commit']['short_id']))
    click.echo('title %s' % (res[0]['commit']['title']))
    for job in res:
        # click.secho("Name: {:s} id: {:d}".format(job['name'], job['id']), bg='black', fg='green')
        # print(json.dumps(job, sort_keys=True, indent=4))
        if job['name'] == jobname:
            click.secho("Found artifact for job {:s}: {:s}".format(job['name'], job['artifacts_file']['filename']), bg='black', fg='green')
            r = requests.get("{:s}/api/v4/projects/{:d}/jobs/{:d}/artifacts".format(
                url, project, job['id']
            ), allow_redirects=True, headers = download_header)
            # print(r.headers)
            if output is None:
                output = job['artifacts_file']['filename']
                pass
            open(output, 'wb').write(r.content)

    sys.exit(0)

if __name__ == '__main__':
    trigger_gitlab_build()
