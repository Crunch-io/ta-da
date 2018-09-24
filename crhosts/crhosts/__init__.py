from __future__ import print_function
import argparse
import csv
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
      subprocess.call('ssh -A -f -N -L %s:%s:%s ec2-user@vpc-nat.eu.crunch.io' % (self.local_port, self.target, self.target_port), shell=True)
      return ('127.0.0.1', self.local_port)

  def __exit__(self, *args, **kwargs):
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


def main():
    parser = argparse.ArgumentParser(
        description='List or connect to Crunch Hosts'
    )
    parser.add_argument('-e', '--environment', nargs=1, default='eu',
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
    tunnelparser.add_argument('INDEX', type=int,
                              help='Tunnel to the given server '
                                   'as listed by list subcommand')
    tunnelparser.add_argument('-i', dest='IDENTITY', 
                              help='Which SSH key to use (IE: ~/.ssh/id_rsa)')
    tunnelparser.add_argument('-p', '--port', dest='PORT', default='2222',
                              help='Tunnel to the given local port')
    tunnelparser.add_argument('-u', '--user', dest='USER', default='root',
                              help='User that should be used to connect '
                                   'to the remot host.')

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
            server = servers[args.INDEX]
        except IndexError:
            print('Invalid Server, valid indexes are:')
            for idx, s in enumerate(servers):
                print('\t', idx, s)
            return
        print('Connecting to', server)
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