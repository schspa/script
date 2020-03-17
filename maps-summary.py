#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   maps-summary.py --- get summary from /proc/<pid>/maps file
#
#   Copyright (C) 2020, schspa, all rights reserved.
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

import re
import os
import sys
import click
#    address           perms offset  dev   inode       pathname
#    00400000-00452000 r-xp 00000000 08:02 173521      /usr/bin/dbus-daemon
MAPS_PATTERN = re.compile(
    r"^(?P<BEGIN>[0-9a-fA-F]+)-(?P<END>[0-9a-fA-F]+)[\s]+(?P<PERM>[\S]+)[\s]+"\
    r"(?P<OFFS>[\S]+)[\s]+(?P<DEV>[\S]+)[\s]+(?P<INODE>[\S]+)[\s]*(?P<PATHNAME>[^\n]*)$")

def parse_file(infile, outfile):
    summary = {}
    for line in infile:
        obj = re.search(MAPS_PATTERN, line)
        if obj is not None:
            key = (obj.group('DEV'), obj.group('INODE'), obj.group('PATHNAME'))
            iterm_size = int(obj.group('END'), 16) - int(obj.group('BEGIN'), 16)
            if key in summary:
                size = summary[key]
                size += iterm_size
            else:
                size = iterm_size
                summary[key] = size;

    outfile.write("{:16s}{:16s}{:16s}{:16s}\n".format('size', 'dev', 'inode', 'path'))
    for k, v in summary.items():
        outfile.write("{:<16d}{:16s}{:16s}{:16s}\n".format(v, k[0], k[1], k[2]))

@click.command()
@click.option('-p', '--parse', 'infile', type=click.File('r'),
              help='/proc/<pid>/maps file to parse.' +
              '(Default: stdin)', required=False, default=sys.stdin)
@click.option('-o', '--output', 'outfile', type=click.File('w'),
              help="Output file path (Default: std output)",
              required=False, default=sys.stdout)
def summary_maps(infile, outfile):
    """summary_maps entry"""
    parse_file(infile, outfile)

if __name__ == '__main__':
    summary_maps()
