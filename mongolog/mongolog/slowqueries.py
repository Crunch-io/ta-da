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
    with tunnel('eu-mongo-01.priveu.crunch.io', 22, 2922) as connection:
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
        self.LINES.append(json.loads(logevent.to_json()))


def main():
    from . import slack 

    tmpf = fetch_logs('/var/log/mongodb/mongod.log')
    try:
        import sys
        sys.argv = sys.argv[:1] + [tmpf, '--slow', '500', '--from', 'now -24hours']
        CrunchMLogFilterTool.LINES = []
        CrunchMLogFilterTool().run()

        text = '\n'.join(' '.join(l['split_tokens']) for l in CrunchMLogFilterTool.LINES)
        r = slack.message(channel="mongo", username="crunchbot", icon_emoji=':worried:',
                          attachments=[{'title': 'MongoDB Queries Summary for past 24 Hours',
                                        'color': "warning", 'text': text}])
        r.raise_for_status()
    finally:
        os.unlink(tmpf)


