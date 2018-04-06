"""
Move documents related to a dataset from one Mongo cluster to another.

Usage:
    ds.mongo-move dump <ds-id> <output-dir>
    ds.mongo-move load <input-dir>
"""
from __future__ import print_function
import os
import subprocess

import docopt
import yaml

CONFIG_FILE = '/var/lib/crunch.io/cr.server-0.conf'


def main():
    args = docopt.docopt(__doc__)
    if args['dump']:
        return do_dump(args)
    if args['load']:
        return do_load(args)
    print("Invalid command.", file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
