from __future__ import print_function
import argparse
import csv
import subprocess
from StringIO import StringIO
import requests
import webbrowser
from paramiko.client import SSHClient, WarningPolicy


class tunnel(object):
  def __init__(self, target, target_port, local_port, killonexit=True):
      self.target = target
      self.target_port = target_port
      self.local_port = local_port
      self.killonexit = killonexit

  def __enter__(self):
      if not self.killonexit:
          # There might be a previous instance running, quit it.
          self._kill_running()
      subprocess.call('ssh -A -f -N -L %s:%s:%s ec2-user@vpc-nat.eu.crunch.io' % (self.local_port, self.target, self.target_port), shell=True)
      return ('127.0.0.1', self.local_port)

  def __exit__(self, *args, **kwargs):
      if self.killonexit:
        self._kill_running()

  def _kill_running(self):
      """Kills currently running portforwarding"""
      subprocess.call('pkill -f "ssh -A -f -N -L %s"' % self.local_port, shell=True)


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


def gather_tags(kind='eu'):
    req = requests.get('http://dev.crunch.io/ec2-hosts.txt', auth=('paster', 'youseeit'))
    tags = set()
    for server in csv.DictReader(StringIO(req.text), delimiter='\t'):
        for role in server['Ansible Role'].split(','):
            tags.add(role.strip())
    return tags


def open_admin(kind='eu'):
    admin_servers = gather_servers(kind=kind, role='webservers')
    if not admin_servers:
        raise ValueError('Unable to identify a valid webserver.')

    


def main():
    parser = argparse.ArgumentParser(
        description='List or connect to Crunch Hosts'
    )
    parser.add_argument('-e', '--environment', default='eu',
                        help='For which environment to act (alpha, eu, ...)')

    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help',
                                       dest='subcommand')

    tagsparser = subparsers.add_parser('tags')

    listparser = subparsers.add_parser('list')                            
    listparser.add_argument('ROLE', help='List existing hosts for given ROLE ' 
                                         '(dbservers, webservers, ...)')

    tunnelparser = subparsers.add_parser('connect')      
    tunnelparser.add_argument('ROLE', help='Work on hosts for given ROLE ' 
                                           '(dbservers, webservers, ...)')                      
    tunnelparser.add_argument('INDEX',
                              help='Tunnel to the given server '
                                   'as listed by list subcommand')
    tunnelparser.add_argument('-i', dest='IDENTITY', 
                              help='Which SSH key to use (IE: ~/.ssh/id_rsa)')
    tunnelparser.add_argument('-p', '--port', dest='PORT', default='2222',
                              help='Tunnel to the given local port')
    tunnelparser.add_argument('-u', '--user', dest='USER', default='root',
                              help='User that should be used to connect '
                                   'to the remot host.')

    adminparser = subparsers.add_parser('admin')      
    adminparser.add_argument('-p', '--port', dest='PORT', default='28081',
                             help='Tunnel to the given local port')


    args = parser.parse_args()
    if args.subcommand == 'tags':
        tags = gather_tags(args.environment)
        for tag in tags:
            print('\t', tag)
    elif args.subcommand == 'list':
        servers = gather_servers(args.environment, args.ROLE)
        for idx, s in enumerate(servers):
            print('\t', idx, s)
    elif args.subcommand == 'connect':
        servers = gather_servers(args.environment, args.ROLE)
        try:
            server_index = int(args.INDEX)
        except ValueError:
            # User requested a predicate
            server = HostPropertyDetector(args).detect(servers, args.INDEX)
            if server is None:
                print("No server matched predicate")
                return
        else:
            # User requested a specific index
            try:
                server = servers[server_index]
            except IndexError:
                print('Invalid Server, valid indexes are:')
                for idx, s in enumerate(servers):
                    print('\t', idx, s)
                return

        print('> Connecting to', server)
        with tunnel(server, 22, args.PORT) as dest:
            command = ('ssh'
                       ' -o UserKnownHostsFile=/dev/null' 
                       ' -o StrictHostKeyChecking=no'
                       ' -p {}'
                       ' {}@{}'.format(dest[1], args.USER, dest[0]))
            if args.IDENTITY:
                command += ' -i {}'.format(args.IDENTITY)
            print(command)
            subprocess.call(command, shell=True)
    elif args.subcommand == 'admin':
        admin_servers = gather_servers(kind=args.environment, 
                                       role='webservers')
        if not admin_servers:
            print('Unable to identify a webserver.')
            return
        server = admin_servers[0]
        print('Connecting to', server)
        with tunnel(server, 8081, args.PORT, 
                    killonexit=False) as dest:
            webbrowser.open('http://{}:{}/'.format(*dest))
    

class HostPropertyDetector(object):
    """Detects properties of an host you are trying to connect to.

    The ``connect`` command allows connecting to a host that has
    a specific property instead of connecting to a given index.

    That is supported by this property detector that checks the host
    properties.

    Each method implemented in this class is a predicate that
    returns ``False`` or ``True`` to verify if the host has
    that property or not.

    All methods accept a ``dest`` argument, which is the pair (address, port)
    you should connect to to reach the host (after tunneling is already in place)
    and a ``user`` argument, which is the user you must use to connect.
    Methods also receive a ``command`` argument, which is the ssh command
    that must be executed to connect to that host. You can append to this
    command to execute scripts on the remote host.
    """
    def __init__(self, args):
        self._args = args

    def detect(self, servers, predicate):
        """Detect a server out of the provided that matches predicate.

        Predicates are provided in the form ``namespace:name`` and
        are verified by ``_namespace_name`` method of this object.
        """
        try:
            predicate = getattr(self, '_'+predicate.replace(':', '_'))
        except AttributeError:
            raise ValueError("Predicate %s not supported" % predicate)

        for server in servers:
            print('> Checking', server)
            with tunnel(server, 22, self._args.PORT) as dest:
                command = ('ssh'
                           ' -o UserKnownHostsFile=/dev/null' 
                           ' -o StrictHostKeyChecking=no'
                           ' -p {}'
                           ' {}@{}'.format(dest[1], self._args.USER, dest[0]))
                if self._args.IDENTITY:
                    command += ' -i {}'.format(self._args.IDENTITY)
                if predicate(dest, self._args.USER, command):
                    return server

    def _mongodb_secondary(self, dest, user, command):
        """Check that the host we are trying to connect to is a mongodb secondary."""
        command = command + """ 'mongo --quiet --eval "rs.status()[\\\""myState\\\""]"'"""
        res = subprocess.check_output(command, shell=True).strip()
        return res == "2"

    def _mongodb_primary(self, dest, user, command):
        """Check that the host we are trying to connect to is a mongodb primary."""
        command = command + """ 'mongo --quiet --eval "rs.status()[\\\""myState\\\""]"'"""
        res = subprocess.check_output(command, shell=True).strip()
        return res == "1"
