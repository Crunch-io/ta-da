from __future__ import print_function

import sys
import os
import time
import tempfile
import subprocess
import requests
import docopt
from . import slack
from .datasetreplay import ENVIRONS, tunnel, admin_url


def main():
    helpstr = """Pick the last modified dataset.

    Usage:
      %(script)s [--skipfile=SKIPFILE] [--env=ENV]
      %(script)s (-h | --help)

    Options:
      -h --help              Show this screen
      --skipfile=SKIPFILE    Skip all the datasets listed into this file
      --env=ENV              Environment against which to run the commands [default: eu]
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    env = arguments['--env']
    skipfile = arguments['--skipfile']
    if skipfile:
        try:
            with open(skipfile) as skipfile:
                skiplist = set((l.strip() for l in skipfile.readlines()))
        except IOError:
            skiplist = {}
    else:
        skiplist = {}

    hosts = ENVIRONS[env]
    with tunnel(hosts[0], 8081, 29081, hosts[1]) as connection:
        resp = requests.get(**admin_url(connection,
                                        '/datasets/?show_all=1&sorting=-modification_time&limit=2000'))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text, file=sys.stderr)
            sys.exit(1)

        datasets = resp.json()['datasets']
        for ds in datasets:
            dataset_id = ds['id']
            if dataset_id in skiplist:
                continue
            else:
                break
        else:
            print('Unable to find a dataset', file=sys.stderr)
            sys.exit(1)

        print(dataset_id)