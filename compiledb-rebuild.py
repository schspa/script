#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0
#
# Schspa (C) 2021
#
# Author: Schspa Shi <schspa@gmail.com>
#
"""A tool for recompile files in compile_commands.json ."""

import argparse
import json
import logging
import os
import re
import subprocess

_DEFAULT_LOG_LEVEL = 'WARNING'

_VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

def parse_arguments():
    """Sets up and parses command-line arguments.

    Returns:
        log_level: A logging level to filter log output.
        directory: The directory to search for .cmd files.
    """
    usage = 'Recompile Single file from kernel .cmd files'
    parser = argparse.ArgumentParser(description=usage)

    compiledb_path_help = ('Path to the compile_commands.json file'
                      '(defaults to the ./compile_commands.json)')
    parser.add_argument('-c', '--compiledb', type=str, help=compiledb_path_help)

    file_pattern_help = ('Regular expression to filter "file" key compile_commands.json'
                      '(defaults to "*")')
    parser.add_argument('-f', '--file', type=str, help=file_pattern_help)

    log_level_help = ('The level of log messages to produce (one of ' +
                      ', '.join(_VALID_LOG_LEVELS) + '; defaults to ' +
                      _DEFAULT_LOG_LEVEL + ')')
    parser.add_argument(
        '--log_level', type=str, default=_DEFAULT_LOG_LEVEL,
        help=log_level_help)

    args = parser.parse_args()

    log_level = args.log_level
    if log_level not in _VALID_LOG_LEVELS:
        raise ValueError('%s is not a valid log level' % log_level)

    compiledb_path = args.compiledb or os.path.join(os.getcwd(), 'compile_commands.json')
    compiledb_path = os.path.abspath(compiledb_path)
    file_pattern = args.file

    return log_level, file_pattern, compiledb_path

def main():
    """Walks through the directory and finds and parses .cmd files."""
    log_level, file_pattern, compiledb_path = parse_arguments()

    level = getattr(logging, log_level)
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)

    logging.debug('log_level %s, file_pattern:  %s, compiledb_path: %s',
                  log_level, file_pattern, compiledb_path)

    filename_matcher = re.compile(file_pattern)

    single_file_filter = None;
    if not os.path.exists(compiledb_path):
        logging.error('compiledb file %s not exists', compiledb_path)
        return

    with open(compiledb_path, 'r') as f:
        compile_commands = json.load(f)
        for compile_command in compile_commands:
            if filename_matcher.match(compile_command['file']):
                logging.info('compile file: %s', compile_command['file'])
                output = subprocess.check_output(compile_command['arguments'],
                                        cwd=compile_command['directory'],
                                        stderr=subprocess.STDOUT).decode("utf-8")
                if output == '':
                    continue
                logging.info(output)
                pass
            pass
        pass
    return

if __name__ == '__main__':
    main()
