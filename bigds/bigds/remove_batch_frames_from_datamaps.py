#!/var/lib/crunch.io/venv/bin/python
"""
Modify a dataset's datamap.zz9 files, removing batch frame entries
See Pivotal ticket #162483895

Usage:
    remove_batch_frames_from_datamap.py [options] <dataset-id>
    remove_batch_frames_from_datamap.py [options] --from-file <dataset-ids-file>

Options:
    --dry-run               Just print statistics, don't make changes
    --config=CONFIG         [default: /var/lib/crunch.io/zz9-0.conf]
    --repo-trash=TRASHDIR   [default: /remote/eu/trash]

Batch frame entries are keys the the datamap that look like this:

    "/__batch_22__/029296.data.zz9"

To make sure a dataset node doesn't get leased while its datamap being modified,
this sets a "__CLEAN" value in the lease map during datamap scanning and
modification.  Datamaps are modified in place both locally and in the repo. Try
to run this script on the zz9 host matching host_map for that dataset.
"""
from __future__ import print_function
import json
import os
import random
import string
import sys

import docopt

from zz9d.stores.simplefs_4 import SimpleFileSystemStore
from zz9lib import lz4lib
from zz9lib.dispatcher import ZZ9Dispatcher


def _make_random_suffix(n=6):
    # Generate a relatively short string that is highly unlikely to collide
    chars = string.ascii_uppercase + string.digits
    return "".join([random.choice(chars) for i in range(n)])


def create_dispatcher(args):
    """
    Return a configured ZZ9Dispatcher instance.
    """
    zz9_config_file = args["--config"]
    with open(zz9_config_file) as f:
        zz9_config = json.load(f)
    assert len(zz9_config) == 1  # assuming only one zone
    _, zone_config = zz9_config.popitem()
    factory_config = zone_config["factories"]
    dispatcher = ZZ9Dispatcher(
        map=factory_config["map"],
        host_map=factory_config["host_map"],
        unreachable_timeout=5,
    )
    return dispatcher


def create_store(args):
    """
    Return a configured SimpleFileSystemStore instance.
    """
    zz9_config_file = args["--config"]
    with open(zz9_config_file) as f:
        zz9_config = json.load(f)
    assert len(zz9_config) == 1  # assuming only one zone
    _, zone_config = zz9_config.popitem()
    factory_config = zone_config["factories"]
    store_config = factory_config["store"]
    store = SimpleFileSystemStore(**store_config)
    return store


class DatasetFixer(object):
    def __init__(self, store, dispatcher, repo_trash, dry_run):
        if dry_run:
            repo_trash = None  # just in case
        else:
            if not os.path.isdir(repo_trash):
                raise ValueError("Repo trash dir dis not exist: {}".format(repo_trash))
            # Ensure that the repo trash is on the same filesystem as the main repo dir
            repodir_dev = os.stat(store.repodir).st_dev
            repo_trash_dev = os.stat(repo_trash).st_dev
            if repodir_dev != repo_trash_dev:
                raise ValueError(
                    "Repo trash dir '{}' not on same filesytem as repo '{}'".format(
                        repo_trash, store.repodir
                    )
                )
        self.store = store
        self.dispatcher = dispatcher
        self.repo_trash = repo_trash
        self.dry_run = dry_run

    def _list_nodes(self, ds_id):
        node_ids = []
        local_ds_dir = self.store.local_root_path({"dataset": ds_id})
        versions_dir = os.path.join(local_ds_dir, "versions")
        if os.path.exists(versions_dir):
            node_ids.extend(os.listdir(versions_dir))
        repo_ds_dir = self.store.repo_root_path({"dataset": ds_id})
        versions_dir = os.path.join(repo_ds_dir, "versions")
        if os.path.exists(versions_dir):
            node_ids.extend(os.listdir(versions_dir))
        return sorted(set(node_ids))

    def _fix_node_datamap(self, node_path, remote=False):
        datamap_path = os.path.join(node_path, "datamap.zz9")
        if remote:
            if not os.path.exists(datamap_path + ".lz4"):
                return 0
            with open(datamap_path + ".lz4", "rb") as f:
                data = lz4lib.lz4framed.decompress(f.read())
        else:
            if not os.path.exists(datamap_path):
                return 0
            with open(datamap_path, "rb") as f:
                data = f.read()
        m = json.loads(data)
        num_changes = 0
        for k in list(m.keys()):
            if k.startswith("/__batch_"):
                num_changes += 1
                if self.dry_run:
                    continue
                del m[k]
        if not self.dry_run and num_changes > 0:
            data = json.dumps(m)
            suffix = _make_random_suffix()
            temp_datamap_path = datamap_path + "_" + suffix
            if remote:
                with open(temp_datamap_path + ".lz4", "wb") as f:
                    f.write(lz4lib.lz4framed.compress(data))
                os.rename(temp_datamap_path + ".lz4", datamap_path + ".lz4")
            else:
                with open(temp_datamap_path, "wb") as f:
                    f.write(data)
                os.rename(temp_datamap_path, datamap_path)
        return num_changes

    def _fix_datamaps_for_dataset(self, ds_id):
        """
        Scan the datamap for each node and modify it if appropriate.
        The caller must make sure no one else is using the dataset!
        Return status dict
        """
        num_local_changes = 0
        num_remote_changes = 0
        node_ids = self._list_nodes(ds_id)
        for node_id in node_ids:
            address = {"dataset": ds_id, "node": node_id}
            local_node_path = self.store.local_node_path(address)
            if os.path.exists(local_node_path):
                if self._fix_node_datamap(local_node_path, remote=False):
                    num_local_changes += 1
            remote_node_path = self.store.repo_node_path(address)
            if self._fix_node_datamap(remote_node_path, remote=True):
                num_remote_changes += 1
        return {
            "num_local_changes": num_local_changes,
            "num_remote_changes": num_remote_changes,
        }

    def _find_and_remove_batch_frame_dirs(self, datafiles_dir, remove_func):
        num_changes = 0
        for variant in os.listdir(datafiles_dir):
            variant_dir = os.path.join(datafiles_dir, variant)
            if not os.path.isdir(variant_dir):
                # Probably the variants.zz9 file
                continue
            for name in os.listdir(variant_dir):
                if not name.startswith("/__batch_"):
                    continue
                num_changes += 1
                if not self.dry_run:
                    remove_func(os.path.join(variant_dir, name))
        return num_changes

    def _move_to_repo_trash(self, target):
        """
        Move the target file or directory into the repo trash directory.
        The target should be on the same filesystem as the repo!
        The target name is given a unique suffix so we don't fail due to name
        collision.
        """
        trash_dir = self.repo_trash
        if not os.path.exists(trash_dir):
            os.makedirs(trash_dir)
        suffix = _make_random_suffix()
        trash_target = os.path.join(
            trash_dir, "{}_{}.trash".format(os.path.basename(target), suffix)
        )
        os.rename(target, trash_target)

    def _move_batch_frame_dirs_to_trash(self, ds_id):
        address = {"dataset": ds_id}
        local_datafiles = os.path.join(self.store.local_root_path(address), "datafiles")
        num_changes = 0
        if os.path.exists(local_datafiles):
            num_changes += self._find_and_remove_batch_frame_dirs(
                local_datafiles, self.store.move_to_local_trash
            )
        repo_datafiles = self.store.repo_datafiles_path(address)
        num_changes += self._find_and_remove_batch_frame_dirs(
            repo_datafiles, self._move_to_repo_trash
        )
        return num_changes

    def fix(self, ds_id):
        """
        Fix the dataset -
        Makes sure the dataset isn't already leased, and prevents leasing while
        datamaps are scanned or changed.
        Return true if the datamap was modified or if batch frames were
        moved to trash, or would have been if dry_run was not set.
        Return false (0) if the dataset was Ok.
        Return None if the dataset was leased and therefore skipped.
        """
        if not self.dispatcher.map.setnx(ds_id, "__CLEAN"):
            print(
                "dataset:",
                ds_id,
                "current leased by factory:",
                self.dispatcher.map.get(ds_id),
            )
            return None
        # If we crash while cleaning, our keys should not live forever
        self.dispatcher.map.expire(ds_id, 600)  # seconds
        try:
            status = self._fix_datamaps_for_dataset(ds_id)
        finally:
            self.dispatcher.map.delete(ds_id)
        # Now that the datamaps are updated we remove batch frame dirs
        num_removes = self._move_batch_frame_dirs_to_trash(ds_id)
        status["num_removes"] = num_removes
        print("dataset:", ds_id, "status:", json.dumps(status, sort_keys=True))
        num_changes = 0
        for k, v in status.items():
            if k.startswith("num_"):
                num_changes += status[k]
        return num_changes


def main():
    args = docopt.docopt(__doc__)
    if args["--from-file"]:
        with open(args["<dataset-ids-file>"]) as f:
            ds_ids = f.read().split()
    else:
        if os.path.isfile(args["<dataset-id>"]):
            raise ValueError(
                "Dataset parameter '{}' is a file. "
                "Did you mean to pass the --from-file option?".format(
                    args["<dataset-id>"]
                )
            )
        ds_ids = [args["<dataset-id>"]]
    repo_trash = args["--repo-trash"]
    store = create_store(args)
    dispatcher = create_dispatcher(args)
    dataset_fixer = DatasetFixer(
        store=store,
        dispatcher=dispatcher,
        repo_trash=repo_trash,
        dry_run=args["--dry-run"],
    )
    num_changed_datasets = 0
    for ds_id in ds_ids:
        if dataset_fixer.fix(ds_id):
            num_changed_datasets += 1
    print("num_datasets:", len(ds_ids), "num_changed_datasets:", num_changed_datasets)
    if args["--dry-run"]:
        print("Dry run, no actual changes made.")


if __name__ == "__main__":
    sys.exit(main())
