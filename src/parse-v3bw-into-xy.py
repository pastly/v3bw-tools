#!/usr/bin/env python3
from lib.parsev3bw import v3bw_fd_into_xy
import sys
# File: parse-v3bw-into-xy.py
# Author: Matt Traudt
# License: CC0
#
# Takes one or more v3bw files as arguments.
#
# Writes to stdout (fingerprint, bandwidth) pairs extracted from the v3bw file.
# Uses lib.parsev3bw.v3bw_fd_into_xy() to do the hard work.
#
# NOTE: If you specify more than one v3bw file, this will do NOTHING to tell
# you when the output from one file stops and the next begins


def main():
    for fname in sys.argv[1:]:
        with open(fname, 'rt') as fd:
            for item in v3bw_fd_into_xy(fd):
                sys.stdout.write('{} {}\n'.format(*item))


if __name__ == '__main__':
    try:
        exit(main())
    except (KeyboardInterrupt, BrokenPipeError):
        pass
