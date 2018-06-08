from __future__ import print_function

import time
import sys
import datetime
import requests
import docopt
from .datasetreplay import ENVIRONS, tunnel, admin_url


def main():
    helpstr = """Clear old datasets of a specific user.

    Usage:
      %(script)s --age=DAYS --user=USEREMAIL [--env=ENV]
      %(script)s (-h | --help)

    Options:
      -h --help              Show this screen
      --age=DAYS             Only preserve datasets more recent than DAYS
      --user=USEREMAIL       Clear oldest datasets for USEREMAIL.
      --env=ENV              Environment against which to run the commands [default: eu]
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    env = arguments['--env']
    user = arguments['--user']
    age = int(arguments['--age'])
    today = datetime.datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=0)

    hosts = ENVIRONS[env]
    with tunnel(hosts[0], 8081, 29085, hosts[1]) as connection:
        resp = requests.get(params={'email': user, 'sorting': '+creation_time', 'limit': 2000},
                            **admin_url(connection, '/datasets/'))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text, file=sys.stderr)
            sys.exit(1)

        datasets = resp.json()['datasets']
        for ds in datasets:
            if ds['owner']['email'] != user:
                print('Dataset %s does not match with expected owner' % ds['id'],
                      file=sys.stderr)
                continue

            try:
                day, daytime = ds['creation_time'].split('T', 1)
                day = datetime.datetime.strptime(day, '%Y-%m-%d')
            except:
                print('Unable to parse creation_time for dataset %s' % ds['id'],
                      file=sys.stderr)
                continue

            dataset_age = today - day
            if dataset_age >= datetime.timedelta(days=age):
                print('Deleting dataset %s (age: %s)' % (ds['id'], dataset_age))
                resp = requests.post(**admin_url(connection, '/datasets/delete/%s' % ds['id']))
                if resp.status_code != 200:
                    print('ERROR: %s' % resp.text, file=sys.stderr)
                # Sleep to allow system resources to focus on anything queued
                # up while we were sending delete queries.
                time.sleep(1.0)
