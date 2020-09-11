from __future__ import print_function

import json
import sys
import time
import subprocess

import datetime
import requests
import docopt
from . import slack

REPLAY_USER = 'systems+replay@crunch.io'
USE_SLACK = False
ENVIRONS = {
    'stable': ('stable-backend.privus.crint.net', 'ubuntu@c3po.aws.crunch.io'),
    'unstable': ('unstable-backend.privus.crint.net', 'ubuntu@c3po.aws.crunch.io'),
    'alpha': ('alpha-backend.priveu.crint.net', 'ec2-user@jump.eu.crint.net'),
    'eu': ('eu-backend.priveu.crint.net', 'ec2-user@jump.eu.crint.net'),
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


def admin_url(connection, path, data=None):
    if not path.startswith('/'):
        path = '/' + path
    r = dict(url='http://%s:%s%s' % (connection[0], connection[1], path),
                headers={'Accept': 'application/json'})

    if data:
        r['data'] = data
    return r

def notify(dataset_id, dataset_name, from_version, message, success=True, skipped=False,
           tracefile=None):
    if USE_SLACK:
        r = slack.message(channel="api", username="crunchbot",
                          icon_emoji=":grinning:" if success else ':worried:' ,
                          attachments=[{
                              'title': 'Dataset Replay Check for %s - %s from %s' % (
                                  dataset_id, dataset_name, from_version
                              ),
                              'text': message
                          }])
        r.raise_for_status()
    else:
        print(message)

    if tracefile is not None:
        with open(tracefile, 'a') as f:
            f.write(json.dumps({
                'date': datetime.datetime.utcnow().strftime('%Y%m%d'),
                'dataset_id': dataset_id, 'from_version': from_version,
                'dataset_name': dataset_name, 'success': success, 'skipped': skipped,
                'message': message,
                'format': '%(dataset_id)s from %(from_version)s: %(message)s'
            })+'\n')


def main():
    global USE_SLACK
    helpstr = """Test Replayability of a dataset.

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
    from_version = arguments['<from_version>']
    USE_SLACK = arguments['--slack']
    env = arguments['--env']
    tracefile = arguments['--tracefile']
    timelimit = arguments['--timelimit']

    if from_version:
        from_revision = from_version.split('__')[-1]
    else:
        from_revision = ''

    if timelimit is not None:
        if not from_revision:
            print('--timelimit is currently only supported when <from_version> is provided too.')
            sys.exit(1)

        timelimit = int(timelimit)

    hosts = ENVIRONS[env]
    with tunnel(hosts[0], 8081, 29081, hosts[1]) as connection:
        print('Fetching Dataset info for %s' % dataset_id)
        resp = requests.get(**admin_url(connection, '/datasets/?dsid=' + dataset_id))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text)
            return

        datasets = resp.json()
        dataset = next(iter(datasets['datasets']), None)
        if not dataset:
            print('Dataset %s not found' % dataset_id)
            return

        if dataset['name'].startswith('AUTOREPLAY '):
            # We don't want to replay our own replays
            print('SKIPPED: %s was a replay' % dataset['name'])
            return

        print('Fetching Actions for Dataset "%s"' % dataset['name'])
        resp = requests.get(**admin_url(connection, '/datasets/%s/actions' % dataset_id))
        if resp.status_code != 200:
            print('ERROR: %s' % resp.text)
            return

        resp = resp.json()
        if from_revision:
            actions_count = 0
            total_time = 0
            for a in resp['actions']:
                if a['hash'] == from_revision:
                    break
                actions_count += 1
                total_time += round(a.get('timing', 0), 3)
        else:
            actions_count = len(resp['actions'])
            total_time = -1

        print('Replaying %s actions (expected %s seconds)...' % (actions_count, total_time))
        if timelimit is not None and total_time > timelimit:
            # notify(dataset_id, dataset['name'], from_revision,
            #       'Skipped: Expected to take %s seconds to replay %s actions' % (
            #           total_time, actions_count
            #       ), success=False, skipped=True, tracefile=tracefile)
            return

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
                if status['message'] == 'There is no savepoint at that revision':
                    # The target savepoint was deleted before we could replay from it.
                    notify(dataset_id, dataset['name'], from_revision,
                           'Skipped: Savepoint deleted before we could start replaying from it',
                           success=False, skipped=True, tracefile=tracefile)
                    return
                elif status['message'].startswith('Trying to modify a deleted dataset'):
                    # If the dataset was deleted we just skip it
                    return

                notify(dataset_id, dataset['name'], from_revision,
                       'Failed: %s' % status['message'],
                       success=False, tracefile=tracefile)
                return

            notify(dataset_id, dataset['name'], from_revision,
                   'Successful: %s' % target_url,
                   success=True, tracefile=tracefile)
        else:
            notify(dataset_id, dataset['name'], from_revision,
                   'Failed: %s' % resp.text,
                   success=False, tracefile=tracefile)

