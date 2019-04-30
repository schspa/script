#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   split-bugreport.py --- split buggreport to separse file
#
#   Copyright (C) 2019, , all rights reserved.
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

SESSION_PATTERN = re.compile(r"(?:^-{1,10}[\s]*)(?P<TITLE>[^\(]+)(?:\()")


def parse_file(infile, outfile):
    try:
        os.mkdir(outfile)
    except OSError as e:
        pass
    output = None
    for line in infile:
        obj = re.search(SESSION_PATTERN, line)
        if obj is not None:
            print(line)
            if output is not None:
                output.close()
            output = open(os.path.join(outfile, obj.group('TITLE').strip(' -=.').replace(' ', '-')), 'w')
            print("session: {:s}".format(obj.group('TITLE')))
        if output is not None:
            output.write(line)

@click.command()
@click.option('-p', '--parse', 'infile', type=click.File('r'),
              help='Build log file to parse compilation commands from.' +
              '(Default: stdin)', required=False, default=sys.stdin)
@click.option('-o', '--output', 'outfile', type=click.STRING,
              help="Output file path (Default: std output)",
              required=False, default='split-bugreport')
def split_bugreport(infile, outfile):
    """compiledb entry"""
    parse_file(infile, outfile)

if __name__ == '__main__':
    split_bugreport()
