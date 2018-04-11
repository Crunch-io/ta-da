"""
Move documents related to a dataset from one Mongo cluster to another.

Usage:
    ds.mongo-move [options] dump <output-dir> <ds-id>...
    ds.mongo-move [options] load <input-dir>

Options:
    --old-mongo    Mongo < 3.4.6, don't use "--uri" option to connect to Mongo.
"""
from __future__ import print_function
import json
import os
import platform
import subprocess

import docopt
from six.moves.urllib.parse import urlparse
import yaml

# Mongo collections that this script will filter, dump, and load
COLLECTIONS = {
    'actions': '{"params.dataset.id": {"$in": DS_IDS}}',
    'analyses_order': '{"dataset_id": {"$in": DS_IDS}}',
    'boxdata': '{"dataset_id": {"$in": DS_IDS}}',
    'comparisons': '{"dataset_id": {"$in": DS_IDS}}',
    'dataset_current_editors': '{"dataset_id": {"$in": DS_IDS}}',
    'dataset_families': '{"crunch_id": {"$in": DS_IDS}}',
    'dataset_permissions': '{"dataset_id": {"$in": DS_IDS}}',
    'dataset_validations': '{"dataset_id": {"$in": DS_IDS}}',
    'datasets': '{"crunch_id": {"$in": DS_IDS}}',
    'deck_analyses': '{"dataset_id": {"$in": DS_IDS}}',
    'deck_order': '{"dataset_id": {"$in": DS_IDS}}',
    'deck_slides': '{"dataset_id": {"$in": DS_IDS}}',
    'decks': '{"dataset_id": {"$in": DS_IDS}}',
    'filter_order': '{"dataset_id": {"$in": DS_IDS}}',
    'filters': '{"dataset_id": {"$in": DS_IDS}}',
    'multitables': '{"dataset_id": {"$in": DS_IDS}}',
    'repair_actions': '{"params.dataset.id": {"$in": DS_IDS}}',
    'slide_ordering': '{"dataset_id": {"$in": DS_IDS}}',
    'snapshots': '{"object_ref.dataset_id": {"$in": DS_IDS}}',
    'streaming': '{"dataset_id": {"$in": DS_IDS}}',
    'user_datasets': '{"dataset_id": {"$in": DS_IDS}}',
    'user_variable_order': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_folders': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_folders2': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_folders_children': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_geodata': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_ordering': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_permissions': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_unique_folders': '{"dataset_id": {"$in": DS_IDS}}',
    'variable_unique_folders2': '{"dataset_id": {"$in": DS_IDS}}',
    'version_tags': '{"dataset_id": {"$in": DS_IDS}}',
    # 'projects',
    # 'project_dataset_order',
    # 'dataset_order',
}

# Algorithm used to determine whether to put a collection on the list above:
# 1. It has more than a handful of documents in prod
# 2. It has 'dataset' in the collection name, OR
#    It has a field named 'dataset' or 'dataset_id' (see is_ds_related_doc())
# 3. It has data for only one dataset (this rules out projects, etc.)

def is_ds_related_doc(doc):
    if doc is None:
        return False
    for name in doc:
        if name in ('dataset', 'dataset_id'):
            return True
    for value in doc.values():
        if isinstance(value, dict):
            if is_ds_related_doc(value):
                return True
    return False


def load_config():
    config_filename = '/var/lib/crunch.io/cr.server-0.conf'
    with open(config_filename) as f:
        return yaml.safe_load(f)


def _add_connection_params(cmd, args, config):
    # Modify cmd, adding Mongo connection parameters based on args and config.
    mongo_url = config['APP_STORE']['URL']
    u = urlparse(mongo_url)
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
    ds_ids = args['<ds-id>']
    assert isinstance(ds_ids, list)
    output_dir = args['<output-dir>']
    config = load_config()
    for collection_name, query in COLLECTIONS.items():
        query_instance = query.replace('DS_IDS', json.dumps(args['<ds-id>']))
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
