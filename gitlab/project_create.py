#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   gitlab-test.py --- Description
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
import sys
import requests
import json
import click


def create_gitlab_project(gitlab_server,
                          gitlab_token,
                          project_path,
                          rootproject=1,
                          verbose=False):
    groups = project_path.split('/')
    id = rootproject
    for group in groups[:-1]:
        if verbose:
            print("Search group: %s at id %d" % (group, id))
            pass

        response = requests.get('%s/api/v4/groups' % (gitlab_server),
                                headers={"PRIVATE-TOKEN": gitlab_token},
                                params={
                                    'search': group,
                                    'id': id
                                })
        response.raise_for_status()
        json_data = json.loads(response.text)
        print(json_data)
        group_json = None
        for resp in json_data:
            print(resp)
            if resp['path'] == group:
                group_json = resp;
                pass
            pass

        if group_json is None:
            if verbose:
                print("Create group\n")
                pass
            response = requests.post(url='%s/api/v4/groups' % (gitlab_server),
                                     data={
                                         'name': group,
                                         'path': group,
                                         'parent_id': id
                                     },
                                     headers={"PRIVATE-TOKEN": gitlab_token})
            response.raise_for_status()
            json_data = json.loads(response.text)
            if verbose:
                print(json_data)
                pass
            id = json_data["id"]
        else:
            id = group_json["id"]
            if verbose:
                print("group is already here, id = %d" % (id))
                pass
            pass
        if verbose:
            print(json_data)
            pass
        pass
    if verbose:
        print("Create Project %s" % (groups[-1]))
        pass
    project = groups[-1]
    response = requests.get('%s/api/v4/groups/%d/projects' %
                            (gitlab_server, id),
                            headers={"PRIVATE-TOKEN": gitlab_token},
                            params={'search': project})
    response.raise_for_status()
    json_data = json.loads(response.text)
    respo_json = None
    for resp in json_data:
        if resp['path'] == project:
            respo_json = resp;
            pass
        pass
    if respo_json is None:
        if verbose:
            print("Project not exists create now\n")
            pass
        response = requests.post(url='%s/api/v4/projects' % (gitlab_server),
                                 data={
                                     'name': project,
                                     'path': project,
                                     'namespace_id': id
                                 },
                                 headers={"PRIVATE-TOKEN": gitlab_token})
        response.raise_for_status()
        json_data = json.loads(response.text)
        if verbose:
            print(json_data)
            pass
        return json_data['ssh_url_to_repo']
        pass
    else:
        if verbose:
            print(respo_json)
            pass
        return respo_json['ssh_url_to_repo']



@click.command()
@click.option('--verbose', is_flag=True, help="Will print verbose messages.")
@click.option('--rootproject', default=1, help='root project id')
@click.option('--server',
              default='https://gitlab.com/',
              help='gitlab server url')
@click.option('--token', default=None, help='gitlab server access token')
@click.argument('path')
def cli(verbose, rootproject, server, token, path):
    return create_gitlab_project(server, token, path, rootproject, verbose)


if __name__ == '__main__':
    cli()
