import csv
import os
import tempfile
import subprocess
from StringIO import StringIO

import requests
from paramiko.client import SSHClient, WarningPolicy


class tunnel(object):
  def __init__(self, target, target_port, local_port):
      self.target = target
      self.target_port = target_port
      self.local_port = local_port

  def __enter__(self):
      subprocess.call('ssh -A -f -N -L %s:%s:%s ec2-user@jump.eu.crint.net' % (self.local_port, self.target, self.target_port), shell=True)
      return ('127.0.0.1', self.local_port)

  def __exit__(self, *args, **kwargs):
      subprocess.call('pkill -f "ssh -A -f -N -L %s"' % self.local_port, shell=True)


def fetch_logs(host, path):
    with tunnel(host, 22, 2922) as connection:
        print('Tunneling Through %s' % (connection,))
        cli = SSHClient()
        cli.load_system_host_keys()
        cli.set_missing_host_key_policy(WarningPolicy())
        cli.connect(*connection, username='root')

        fd, tmpath = tempfile.mkstemp()
        os.close(fd)

        try:
            sftp = cli.open_sftp()
            sftp.get(path, tmpath)
            return tmpath
        except:
            os.unlink(tmpath)
            raise


import json
from mtools.mlogfilter.mlogfilter import MLogFilterTool
class CrunchMLogFilterTool(MLogFilterTool):
      LINES = []
      def _outputLine(self, logevent, length=None, human=False):
        if self.args['timestamp_format'] != 'none':
            logevent._reformat_timestamp(self.args['timestamp_format'], force=True)
        if any(self.args['timezone']):
            if self.args['timestamp_format'] == 'none':
                self.args['timestamp_format'] = logevent.datetime_format
            logevent._reformat_timestamp(self.args['timestamp_format'], force=True)

        data = json.loads(logevent.to_json())
        line_str = data['line_str'].lower()
        if 'getmore' in line_str:
            # In theory we are interested in getmore operations, but they
            # screw up stats due to migrate host dumps
            return

        if 'nreturned' not in data or data.get('operation') == 'update':
            # For now focus on reads, will have to monitor more once reads are sane
            return

        if "oplog.rs" in line_str or "local.system.replset" in line_str:
            # We don't care for replication queries right now
            return

        if "io_crunch_celery_broker" in line_str or "celery_taskmeta" in line_str:
            # Avoid tracking queries by the tasks datadog agent
            return

        self.LINES.append(data)


def gather_servers(kind='eu', role='dbservers'):
    req = requests.get('http://dev.crunch.io/ec2-hosts.txt', auth=('paster', 'youseeit'))
    servers = []
    for server in csv.DictReader(StringIO(req.text), delimiter='\t'):
        if kind != server['System']:
            continue
        if role not in server['Ansible Role']:
            continue
        servers.append(server['Name'])
    return servers


def main():
    from . import slack

    with tempfile.NamedTemporaryFile('rw+b') as tmpf:
        for server in gather_servers():
            serverlog = fetch_logs(server, '/var/log/mongodb/mongod.log')
            try:
                with open(serverlog) as f:
                    tmpf.write(f.read())
                tmpf.write('\n')
            finally:
                os.unlink(serverlog)
        tmpf.seek(0)

        import sys
        # We need all this to fake MLogFilterTool to think it got called with an input and some arguments
        sys.stdin = tmpf
        sys.argv = sys.argv[:1] + ['--slow', '500', '--from', 'now -24hours']
        CrunchMLogFilterTool.LINES = []
        CrunchMLogFilterTool().run()

        text = '\n\n'.join('%s in %sms -> %s...' % (l.get('nreturned', '?'), l['duration'], l['line_str'][:384]) for l in CrunchMLogFilterTool.LINES)
        if text.strip():
            r = slack.message(channel="mongo", username="crunchbot", icon_emoji=':worried:',
                              attachments=[{'title': 'MongoDB Slow Queries for past 24 Hours',
                                            'color': "warning", 'text': '```' + text[:8192] + '```',
                                            "mrkdwn_in": ["text", "fallback"]}])
        else:
            r = slack.message(channel="mongo", username="crunchbot", icon_emoji=":grinning:",
                              attachments=[{'title': 'MongoDB Slow Queries for past 24 Hours',
                                            'text': 'No query over 500ms'}])
        r.raise_for_status()

