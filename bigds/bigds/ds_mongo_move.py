"""
Move documents related to a dataset from one Mongo cluster to another.

Usage:
    ds.mongo-move dump <ds-id> <archive-filename>
    ds.mongo-move load <archive-filename>
"""
from __future__ import print_function
import os
import platform
import string
import subprocess

import docopt
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
    # 'dataset_order': {},
}


def load_config():
    config_filename = '/var/lib/crunch.io/cr.server-0.conf'
    with open(config_filename) as f:
        return yaml.safe_load(f)


def do_dump(args):
    ds_id = args['<ds-id>']
    archive_filename = args['<archive-filename>']
    config = load_config()
    mongo_url = config['APP_STORE']['URL']
    for collection_name, query in COLLECTIONS.items():
        query_instance = string.Template(query).substitute(ds_id=ds_id)
        cmd = [
            'mongodump',
            '--uri', mongo_url,
            '--collection', collection_name,
            '--query', query_instance,
            '--archive={}'.format(archive_filename),
        ]
        print(subprocess.list2cmdline(cmd))
        subprocess.check_call(cmd)


def do_load(args):
    if 'mongo' in platform.node().lower():
        raise RuntimeError(
            "Hostname '{}' looks like a production mongo system. Aborting."
            .format(platform.node()))
    archive_filename = args['<archive-filename>']
    config = load_config()
    mongo_url = config['APP_STORE']['URL']
    cmd = [
        'mongorestore',
        '--uri', mongo_url,
        '--archive={}'.format(archive_filename),
    ]
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
