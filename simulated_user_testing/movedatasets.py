import json
import sys
import docopt
import requests
from datasetreplay.datasetreplay import admin_url, ENVIRONS, tunnel


def main():
    global USE_SLACK
    helpstr = """Move Dataset from one environment to another.

    Usage:
      %(script)s <dsid> [<from_version>] [--slack] [--env=ENV] [--tracefile=TRACEFILE] [--timelimit=SECONDS]
      %(script)s (-h | --help)

    Arguments:
      dsid ID of the dataset that should be replayed
      from_version revision from which the dataset replay should be tested.
                   By default datasets replay from the origin.

    Options:
      -h --help               Show this screen
      --slack                 Send messages to slack
      --env=ENV               Environment against which to run the commands [default: eu]
      --tracefile=TRACEFILE   Save replay logs to a file.
      --timelimit=SECONDS     Limit maximum allowed history length to SECONDS seconds.
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    dataset_id = arguments['<dsid>']
    #from_version = arguments['<from_version>']
    USE_SLACK = arguments['--slack']
    env = arguments['--env']
    tracefile = arguments['--tracefile']
    timelimit = arguments['--timelimit']

    #if from_version:
    #    from_revision = from_version.split('__')[-1]
    #else:
    #    from_revision = ''

    hosts = ENVIRONS[env]
    with tunnel(hosts[0], 8081, 29081, hosts[1]) as connection:
        print('Fetching Dataset info for %s' % dataset_id)
        resp = requests.get(**admin_url(connection, '/datasets/%s' % dataset_id))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text)
            return

        import ipdb; ipdb.set_trace()
        return
        print("bundling dataset: %s on environ env: %s..." % (dataset_id, env))
        resp = requests.post(**admin_url(connection, '/bundles/makebundle/',
                             data={'dataset': dataset_id}))
        progress_url = '/'.join(json.loads(resp.text)['value'].split('/')[3:])
        requests.get(**admin_url(connection, progress_url))
        print("done.")
        import ipdb; ipdb.set_trace()


if __name__ == '__main__':
    main()