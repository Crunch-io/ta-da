#!/usr/bin/env python
"""
Copy ownership and permissions from one dataset to another.

Usage:
    ds_copy_perms.py [options] <source-ds-id> <destination-ds-id>

Options:
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]
"""
from __future__ import print_function
import os
import sys

import docopt
from magicbus import bus
from magicbus.plugins import loggers

from cr.lib import exceptions
from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets.copy import (
    DATASET_COLLECTIONS_UNVERSIONED,
    SKIP,
    DatasetMetadataCopier,
)
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib.entities.decks import DeckOrder
from cr.lib.entities.permissions import Permission
from cr.lib.entities.userprefs import UserDatasetPreferences
from cr.lib.entities.variables.order import UserVariableOrder
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings
from cr.lib import stores
from cr.lib.stores.mongo import allow_reading_unversioned


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args['--cr-lib-config']
    settings.update(load_settings(settings_yaml))
    startup()


class DatasetPermissionsCopier(DatasetMetadataCopier):

    def copy_perms_only(self, strategy=SKIP):
        self.trace_log.append("Origin dataset: %s" % (self.origin.id))
        self.trace_log.append("Target dataset: %s" % (self.target.id))

        to_copy, docs_not_copied = self.prepare_docs_to_copy(
            variable_id_map,
            all_not_copied,
        )
        self.copy_docs(
            to_copy,
            docs_not_copied,
            variable_id_map,
            all_not_copied,
            strategy,
        )
        self.copy_dataset_attrs(variable_id_map, all_not_copied)


def _build_query(ds, collection):
    if collection == 'access_permissions':
        return {'target': entity_path_step(ds.origin)}, False
    query = {'dataset_id': ds.origin.id}
    return query


def ds_copy_perms(source_ds_id, destination_ds_id):
    try:
        origin = Dataset.find_by_id(id=source_ds_id, version='master__tip')
    except exceptions.NotFound:
        print("Source dataset not found:", source_ds_id, file=sys.stderr)
        return 1
    try:
        target = Dataset.find_by_id(id=destination_ds_id, version='master__tip')
    except exceptions.NotFound:
        print("Destination dataset not found:", destination_ds_id,
              file=sys.stderr)
        return 1
    for storename in DATASET_COLLECTIONS_UNVERSIONED:
        store = getattr(stores.stores, storename)
        query = _build_query(storename)
        with allow_reading_unversioned(
            Permission, UserDatasetPreferences, UserVariableOrder, DeckOrder
        ):
            docs = store.find_all(query)


def main():
    args = docopt.docopt(__doc__)
    source_ds_id = args['<source-ds-id>']
    destination_ds_id = args['<destination-ds-id>']
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)
    return ds_copy_perms(source_ds_id, destination_ds_id)


if __name__ == '__main__':
    sys.exit(main())
