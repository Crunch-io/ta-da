from __future__ import print_function

import json
import sys
import time
import subprocess

import datetime
import requests

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


def fqdn_link(env, path):
    if not path.startswith('/'):
        path = '/' + path
    return "https://%s.superadmin.crint.net%s" % (env, path)