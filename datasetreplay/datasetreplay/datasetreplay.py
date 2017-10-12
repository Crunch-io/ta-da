from __future__ import print_function

import sys
import time
import subprocess
import requests
import docopt
from . import slack

REPLAY_USER = 'systems+replay@crunch.io'
USE_SLACK = False
ENVIRONS = {
    'unstable': ('localhost', 'ubuntu@unstable-backend.crunch.io'),
    'stable': ('localhost', 'ubuntu@stable-backend.crunch.io'),
    'alpha': ('alpha-backend-39.priveu.crunch.io', 'ec2-user@vpc-nat.eu.crunch.io'),
    'eu': ('eu-backend-178.priveu.crunch.io', 'ec2-user@vpc-nat.eu.crunch.io'),
    'vagrant': (None, None)
}


class tunnel(object):
    def __init__(self, target, target_port, local_port, bastion):
        self.target = target
        self.target_port = target_port
        self.local_port = local_port
        self.bastion = bastion

    def __enter__(self):
        if self.target is None and self.bastion is None:
            return '127.0.0.1', self.target_port

        print('Tunnel to %s through %s' % (self.target, self.bastion), file=sys.stderr)
        subprocess.call(
            'ssh -A -f -N -L %s:%s:%s %s' % (self.local_port, self.target, self.target_port, self.bastion),
            shell=True
        )
        return '127.0.0.1', self.local_port

    def __exit__(self, *args, **kwargs):
        if self.target is None and self.bastion is None:
            return

        subprocess.call('pkill -f "ssh -A -f -N -L %s"' % self.local_port, shell=True)


def admin_url(connection, path):
    if not path.startswith('/'):
        path = '/' + path
    return dict(url='http://%s:%s%s' % (connection[0], connection[1], path),
                headers={'Accept': 'application/json'})


def notify(dataset_id, dataset_name, from_version, message, success=True):
    if USE_SLACK:
        r = slack.message(channel="sentry", username="crunchbot",
                          icon_emoji=":grinning:" if success else ':worried:' ,
                          attachments=[{'title': 'Dataset Replay Check for %s - %s from %s' % (dataset_id, dataset_name, from_version),
                                        'text': message}])
        r.raise_for_status()
    else:
        print(message)


def main():
    global USE_SLACK
    helpstr = """Test Replayability of a dataset.

    Usage:
      %(script)s <dsid> [<from_version>] [--slack] [--env=ENV]
      %(script)s (-h | --help)

    Arguments:
      dsid ID of the dataset that should be replayed
      from_version revision from which the dataset replay should be tested.
                   By default datasets replay from the origin.

    Options:
      -h --help    Show this screen
      --slack      Send messages to slack
      --env=ENV    Environment against which to run the commands [default: eu]
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    dataset_id = arguments['<dsid>']
    from_version = arguments['<from_version>']
    USE_SLACK = arguments['--slack']
    env = arguments['--env']

    if from_version:
        from_revision = from_version.split('__')[-1]
    else:
        from_revision = ''

    hosts = ENVIRONS[env]
    with tunnel(hosts[0], 8081, 29081, hosts[1]) as connection:
        resp = requests.get(**admin_url(connection, '/datasets/?dsid=' + dataset_id))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text)
            return

        datasets = resp.json()
        dataset = next(iter(datasets['datasets']), None)
        if not dataset:
            print('Dataset %s not found' % dataset_id)
            return

        print('Fetching Actions for Dataset "%s"' % dataset['name'])
        resp = requests.get(**admin_url(connection, '/datasets/%s/actions' % dataset_id))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text)
            return

        resp = resp.json()
        if from_revision:
            actions_count = 0
            for a in resp['actions']:
                if a['hash'] == from_revision:
                    break
                actions_count += 1
        else:
            actions_count = len(resp['actions'])

        print('Replaying %s actions...' % actions_count)
        resp = requests.post(
            data={
                'dataset_name': 'AUTOREPLAY %s - %s' % (int(time.time()), dataset['name']),
                'dataset_owner': REPLAY_USER,
                'from_revision': from_revision
            },
            allow_redirects=False,
            **admin_url(connection, '/datasets/%s/actions/replay' % dataset_id)
        )
        if resp.status_code in (202, ):
            # Progress response, the replay is proceeding asynchronously.
            progress_url = resp.json()['value']
            target_url = resp.headers['Location']
            status = {'progress': 0, 'message': ''}
            while -1 < status['progress'] < 100:
                status.update(requests.get(progress_url).json()['value'])
                print('    %(progress)s%% - %(message)s' % status)
                time.sleep(5.0)

            if status['progress'] == -1:
                notify(dataset_id, dataset['name'], from_revision,
                       'Failed to replay dataset: %s' % status['message'],
                       success=False)
                return

            notify(dataset_id, dataset['name'], from_revision,
                   'Successfully replayed dataset at: %s' % target_url,
                   success=True)
        else:
            notify(dataset_id, dataset['name'], from_revision,
                   'Failed to replay dataset: %s' % resp.text,
                   success=False)

