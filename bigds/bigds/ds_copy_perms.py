#!/usr/bin/env python
"""
Copy ownership and permissions from one dataset to another.
The intended use case is to copy permissions from a source dataset to a
replayed copy.

Usage:
    ds_copy_perms.py [options] ls <source-ds-id>
    ds_copy_perms.py [options] cp <source-ds-id> <target-ds-id>

Options:
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]
    --force                   Continue even if permissions appear to have
                              already been copied before.
"""
from __future__ import print_function
import os
import pprint
import sys

import docopt
from magicbus import bus
from magicbus.plugins import loggers
import six

from cr.lib import exceptions
from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets.copy import (
    DATASET_COLLECTIONS_UNVERSIONED,
)
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib.entities.datasets.dataset.currenteditor import DatasetCurrentEditor
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings
from cr.lib import stores
from cr.lib.stores.metadata.extract import generate_query
from cr.lib.utils.entitypaths import entity_path_step


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args['--cr-lib-config']
    settings.update(load_settings(settings_yaml))
    startup()


def _build_query(ds, collection_name):
    # TODO: Remove this special case after #160142829 is deployed.
    if collection_name == 'access_permissions':
        return {'target': entity_path_step(ds)}
    return generate_query(collection_name, ds.id)


def _to_dict(obj):
    # Convert obj from possibly a SON to a regular dict for better printing
    # Also convert u'' keys to regular strings
    if isinstance(obj, dict):
        result = {}
        for k, v in six.iteritems(obj):
            if six.PY2:
                if isinstance(k, six.text_type):
                    k = k.encode('utf-8')
            result[k] = _to_dict(v)
    elif isinstance(obj, list):
        result = [_to_dict(i) for i in obj]
    else:
        result = obj
    return result


def ds_list_perms(ds_id):
    try:
        ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    except exceptions.NotFound:
        print("Source dataset not found:", ds_id, file=sys.stderr)
        return 1
    print("Dataset mongo record:")
    pprint.pprint(_to_dict(ds._data))
    current_editors = DatasetCurrentEditor.find_all({'dataset_id': ds_id})
    # Note: There should be exactly one current_editor record!
    for current_editor in current_editors:
        user = current_editor.user
        if user is None:
            print("Dataset current editor: Nobody is editing")
        else:
            print("Dataset current editor: {} <{}> ({})"
                  .format(user.name, user.email, user.id))
    for storename in DATASET_COLLECTIONS_UNVERSIONED:
        store = getattr(stores.stores, storename)
        query = _build_query(ds, storename)
        docs = store.find_all(query)
        print("storename:", storename, "num_docs:", len(docs))
        for doc in docs:
            pprint.pprint(_to_dict(doc))
    return 0


def ds_copy_perms(source_ds_id, target_ds_id, force=False):
    try:
        source = Dataset.find_by_id(id=source_ds_id, version='master__tip')
    except exceptions.NotFound:
        print("Source dataset not found:", source_ds_id, file=sys.stderr)
        return 1

    try:
        target = Dataset.find_by_id(id=target_ds_id, version='master__tip')
    except exceptions.NotFound:
        print("Target dataset not found:", target_ds_id,
              file=sys.stderr)
        return 1

    if (not force
            and source.owner_id == target.owner_id
            and source.owner_type == target.owner_type):
        raise ValueError(
            "Attempting to copy permissions to dataset with same ownership")
    print("Target owner type:", target.owner_type, "Target owner ID:",
          target.owner_id)

    # Grab the source dataset current editor
    try:
        current_editor_id = DatasetCurrentEditor.find_one(
            {'dataset_id': source.id}).user_id
    except exceptions.NotFound:
        current_editor_id = None

    # Copy the non-versioned fields
    update = {
        'name': source.name,
        'account_id': source.account_id,
    }
    for attrname in Dataset.SAVEPOINT_EXCLUSIONS['datasets']:
        update[attrname] = getattr(source, attrname)
    result = stores.stores.datasets.update_many({'id': target.id}, update)
    print("Result of updating datasets: matched_count {} modified_count {}"
          .format(result.matched_count, result.modified_count))

    # Set the target current editor
    DatasetCurrentEditor.update_many({
        'dataset_id': target.id
    }, {
        'user_id': current_editor_id
    })

    # Copy the rest of the unversioned collections
    for storename in DATASET_COLLECTIONS_UNVERSIONED:
        store = getattr(stores.stores, storename)
        src_docs = list(store.find_all(_build_query(source, storename)))
        dst_docs = list(store.find_all(_build_query(target, storename)))
        if target.owner_type == 'User':
            # Delete pre-existing docs (user_datasets) with wrong user_id
            doc_ids_to_del = [
                doc['_id'] for doc in dst_docs
                if 'user_id' in doc and doc['user_id'] == target.owner_id
            ]
            print("Deleting", len(doc_ids_to_del), "pre-existing",
                  storename, "docs")
            store.delete_many({'_id': {'$in': doc_ids_to_del}})
        for doc in src_docs:
            del doc['_id']
            del doc['id']
            doc['dataset_id'] = target.id
        print("Inserting", len(src_docs), storename, "docs")
        for doc in src_docs:
            try:
                store.insert(doc)
            except exceptions.MultipleItemsFound:
                print("Skipped duplicate doc:", _to_dict(doc))


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)
    source_ds_id = args['<source-ds-id>']
    if args['ls']:
        return ds_list_perms(source_ds_id)
    if args['cp']:
        target_ds_id = args['<target-ds-id>']
        return ds_copy_perms(source_ds_id, target_ds_id,
                             force=args['--force'])
    print("Unknown command.", file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())