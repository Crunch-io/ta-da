from __future__ import print_function

import sys
import requests
import docopt
from .datasetreplay import ENVIRONS, tunnel, admin_url


def main():
    helpstr = """Given a dataset provides the list of savepoints.

    Usage:
      %(script)s <dsid> [--env=ENV]
      %(script)s (-h | --help)

    Arguments:
      dsid ID of the dataset for which to list the savepoints.

    Options:
      -h --help              Show this screen
      --env=ENV              Environment against which to run the commands [default: eu]
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    env = arguments['--env']
    dataset_id = arguments['<dsid>']

    hosts = ENVIRONS[env]
    with tunnel(hosts[0], 8081, 29081, hosts[1]) as connection:
        resp = requests.get(**admin_url(connection, '/datasets/%s/versions' % dataset_id))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text, file=sys.stderr)
            sys.exit(1)

        versions = resp.json()['versions']
        for version in versions:
            print(version['versiontag']['version'])
