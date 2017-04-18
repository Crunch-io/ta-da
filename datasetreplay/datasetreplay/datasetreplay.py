import sys
import os
import tempfile
import subprocess
import requests
import docopt


class tunnel(object):
    def __init__(self, target, target_port, local_port):
        self.target = target
        self.target_port = target_port
        self.local_port = local_port

    def __enter__(self):
        subprocess.call(
            'ssh -A -f -N -L %s:%s:%s ec2-user@vpc-nat.eu.crunch.io' % (self.local_port, self.target, self.target_port),
            shell=True
        )
        return '127.0.0.1', self.local_port

    def __exit__(self, *args, **kwargs):
        subprocess.call('pkill -f "ssh -A -f -N -L %s"' % self.local_port, shell=True)


def admin_url(connection, path):
    return dict(url='http://localhost:%s/%s' % (connection[1], path), headers={'Accept': 'application/json'})


def main():
    replay_user = 'systems+replay@crunch.io'
    helpstr = """Test Replayability of a dataset.

    Usage:
      %(script)s <dsid>
      %(script)s (-h | --help)

    Arguments:
      dsid ID of the dataset that should be replayed

    Options:
      -h --help     Show this screen
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:3])
    dataset_id = arguments['<dsid>']

    from . import slack 
    with tunnel('eu-backend.priveu.crunch.io', 8081, 2981) as connection:
        datasets = requests.get(**admin_url(connection, '/datasets/?dsid=' + dataset_id)).json()
        dataset = next(iter(datasets['datasets']), None)
        if not dataset:
            print('Dataset %s not found' % dataset_id)
            return

        
