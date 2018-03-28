import os
import tempfile
import subprocess
from paramiko.client import SSHClient, WarningPolicy


class tunnel(object):
  def __init__(self, target, target_port, local_port):
      self.target = target
      self.target_port = target_port
      self.local_port = local_port

  def __enter__(self):
      subprocess.call('ssh -A -f -N -L %s:%s:%s ec2-user@vpc-nat.eu.crunch.io' % (self.local_port, self.target, self.target_port), shell=True)
      return ('127.0.0.1', self.local_port)

  def __exit__(self, *args, **kwargs):
      subprocess.call('pkill -f "ssh -A -f -N -L %s"' % self.local_port, shell=True)


def fetch_logs(path):
    with tunnel('eu-mongo-2-59.priveu.crunch.io', 22, 2922) as connection:
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
        if data['operation'] in ('getmore', ):
            # In theory we are interested in getmore operations, but they
            # screw up stats due to migrate host dumps
            return

        if data['operation'] != 'query':
            # For now focus on reads, will have to monitor more once reads are sane
            return
        
        self.LINES.append(data)


def main():
    from . import slack 

    tmpf = fetch_logs('/var/log/mongodb/mongod.log')
    try:
        import sys
        # We need all this to fake MLogFilterTool to think it got called with an input and some arguments
        sys.stdin = open(tmpf)
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
    finally:
        os.unlink(tmpf)


