"""
Move documents related to a dataset from one Mongo cluster to another.

Usage:
    ds.mongo-move [options] dump <ds-id> <output-dir>
    ds.mongo-move [options] load <input-dir>

Options:
    --old-mongo    Mongo < 3.4.6, don't use "--uri" option to connect to Mongo.
"""
from __future__ import print_function
import os
import platform
import string
import subprocess

import docopt
from six.moves.urllib.parse import urlparse
import yaml

# Mongo collections that this script will filter, dump, and load
COLLECTIONS = {
    'actions': '{"params.dataset.id": "$ds_id"}',
    'user_datasets': '{"dataset_id": "$ds_id"}',
    'dataset_validations': '{"dataset_id": "$ds_id"}',
    'dataset_current_editors': '{"dataset_id": "$ds_id"}',
    'dataset_permissions': '{"dataset_id": "$ds_id"}',
    'datasets': '{"crunch_id": "$ds_id"}',
    'dataset_families': '{"crunch_id": "$ds_id"}',
    # 'projects',
    # 'project_dataset_order',
    # 'dataset_order',
}


def load_config():
    config_filename = '/var/lib/crunch.io/cr.server-0.conf'
    with open(config_filename) as f:
        return yaml.safe_load(f)


def _add_connection_params(cmd, args, config):
    # Modify cmd, adding Mongo connection parameters based on args and config.
    mongo_url = config['APP_STORE']['URL']
    if args['--old-mongo']:
        # For Mongo < 3.4.6, the --uri parameter is not available
        db_name = u.path.lstrip('/')
        connection_params = []
        if u.hostname:
            connection_params.extend(['--host', u.hostname])
        if u.port:
            connection_params.extend(['--port', str(u.port)])
        if db_name:
            connection_params.extend(['--db', db_name])
        if u.username:
            connection_params.extend(['--username', u.username])
        if u.password:
            connection_params.extend(['--password', u.password])
        cmd[1:1] = connection_params
    else:
        cmd[1:1] = ['--uri', mongo_url]


def do_dump(args):
    ds_id = args['<ds-id>']
    output_dir = args['<output-dir>']
    config = load_config()
    for collection_name, query in COLLECTIONS.items():
        query_instance = string.Template(query).substitute(ds_id=ds_id)
        cmd = [
            'mongodump',
            '--collection', collection_name,
            '--query', query_instance,
            '--out', output_dir,
        ]
        _add_connection_params(cmd, args, config)
        print(subprocess.list2cmdline(cmd))
        subprocess.check_call(cmd)


def do_load(args):
    input_dir = args['<input-dir>']
    config = load_config()
    mongo_url = config['APP_STORE']['URL']
    u = urlparse(mongo_url)
    if u.hostname is not None and 'mongo' in u.hostname.lower():
        raise RuntimeError(
            "Hostname '{}' looks like a production mongo system. Aborting."
            .format(u.hostname))
    cmd = [
        'mongorestore',
        '--noIndexRestore',
        '--noOptionsRestore',
        input_dir,
    ]
    _add_connection_params(cmd, args, config)
    print(subprocess.list2cmdline(cmd))
    subprocess.check_call(cmd)


def main():
    args = docopt.docopt(__doc__)
    if args['dump']:
        return do_dump(args)
    if args['load']:
        return do_load(args)
    print("Invalid command.", file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
