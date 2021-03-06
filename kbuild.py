#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0
#
# Schspa (C) 2021
#
# Author: Schspa Shi <schspa@gmail.com>
#
"""A tool for recompile single file in the Linux kernel."""

import argparse
import json
import logging
import os
import re

_DEFAULT_LOG_LEVEL = 'WARNING'

_FILENAME_PATTERN = r'^\..*\.cmd$'
_LINE_PATTERN = r'^cmd_[^ ]*\.o := (.* )([^ ]*\.c)$'
_VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

def parse_arguments():
    """Sets up and parses command-line arguments.

    Returns:
        log_level: A logging level to filter log output.
        directory: The directory to search for .cmd files.
    """
    usage = 'Recompile Single file from kernel .cmd files'
    parser = argparse.ArgumentParser(description=usage)

    kernel_directory_help = ('Path to the kernel source directory '
                      '(defaults to the working directory)')
    parser.add_argument('-k', '--kernel', type=str, help=kernel_directory_help)

    directory_help = ('Path related to the kernel source directory to search '
                      '(defaults to kernel source directory)')
    parser.add_argument('-d', '--directory', type=str, help=directory_help)

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

    kernel_directory = args.kernel or os.getcwd()
    kernel_directory = os.path.abspath(kernel_directory)
    directory = os.path.join(kernel_directory, args.directory) or kernel_directory
    directory = os.path.abspath(directory)

    return log_level, directory, kernel_directory


def process_line(root_directory, file_directory, command_prefix, relative_path):
    """Extracts information from a .cmd line and creates an entry from it.

    Args:
        root_directory: The directory that was searched for .cmd files. Usually
            used directly in the "directory" entry in compile_commands.json.
        file_directory: The path to the directory the .cmd file was found in.
        command_prefix: The extracted command line, up to the last element.
        relative_path: The .c file from the end of the extracted command.
            Usually relative to root_directory, but sometimes relative to
            file_directory and sometimes neither.

    Returns:
        An entry to append to compile_commands.

    Raises:
        ValueError: Could not find the extracted file based on relative_path and
            root_directory or file_directory.
    """
    # The .cmd files are intended to be included directly by Make, so they
    # escape the pound sign '#', either as '\#' or '$(pound)' (depending on the
    # kernel version). The compile_commands.json file is not interepreted
    # by Make, so this code replaces the escaped version with '#'.
    prefix = command_prefix.replace('\#', '#').replace('$(pound)', '#')

    cur_dir = root_directory
    expected_path = os.path.join(cur_dir, relative_path)
    if not os.path.exists(expected_path):
        # Try using file_directory instead. Some of the tools have a different
        # style of .cmd file than the kernel.
        cur_dir = file_directory
        expected_path = os.path.join(cur_dir, relative_path)
        if not os.path.exists(expected_path):
            raise ValueError('File %s not in %s or %s' %
                             (relative_path, root_directory, file_directory))
    return {
        'directory': cur_dir,
        'file': relative_path,
        'command': prefix + relative_path,
    }


def main():
    """Walks through the directory and finds and parses .cmd files."""
    log_level, directory, kernel_directory = parse_arguments()

    level = getattr(logging, log_level)
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)

    logging.debug('log_level %s, direcoty:  %s, kernel_directory: %s',
                                     log_level, directory, kernel_directory)

    filename_matcher = re.compile(_FILENAME_PATTERN)
    line_matcher = re.compile(_LINE_PATTERN)

    single_file_filter = None;
    if os.path.isfile(directory):
        single_file_filter = directory
        directory = os.path.dirname(directory)
        pass

    compile_commands = []
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            if not filename_matcher.match(filename):
                continue
            filepath = os.path.join(dirpath, filename)

            with open(filepath, 'rt') as f:
                for line in f:
                    result = line_matcher.match(line)
                    if not result:
                        continue

                    try:
                        entry = process_line(kernel_directory, dirpath,
                                             result.group(1), result.group(2))
                        compile_commands.append(entry)
                    except ValueError as err:
                        logging.info('Could not add line from %s: %s',
                                     filepath, err)
    for compile_command in compile_commands:
        if single_file_filter is not None:
            if single_file_filter != os.path.join(compile_command['directory'],
                                                  compile_command['file']):
                continue
        exec_command = "cd {:s} && {:s}".format(compile_command['directory'],
                                                compile_command['command'])
        print(exec_command)
        os.system(exec_command)
        if single_file_filter is not None:
            break

if __name__ == '__main__':
    main()
