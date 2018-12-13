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
    --quick-dirty           Don't run code in factory, run directly.
                            Only do this if you know the datasets are not in
                            use.

Batch frame entries are keys the the datamap that look like this:

    "/__batch_22__/029296.data.zz9"

If running with --quick-dirty:
    Make sure no one tries to use the datasets while you run this.
    Datamaps are modified locally if they exist locally
    Datamaps are modified in place in the repo
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


def _make_random_suffix(n=6):
    # Generate a relatively short string that is highly unlikely to collide
    chars = string.ascii_uppercase + string.digits
    return "".join([random.choice(chars) for i in range(n)])


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


def list_nodes(store, ds_id):
    node_ids = []
    local_ds_dir = store.local_root_path({"dataset": ds_id})
    versions_dir = os.path.join(local_ds_dir, "versions")
    if os.path.exists(versions_dir):
        node_ids.extend(os.listdir(versions_dir))
    repo_ds_dir = store.repo_root_path({"dataset": ds_id})
    versions_dir = os.path.join(repo_ds_dir, "versions")
    if os.path.exists(versions_dir):
        node_ids.extend(os.listdir(versions_dir))
    return sorted(set(node_ids))


def _quick_dirty_fix_datamap(args, node_path, remote=False):
    datamap_path = os.path.join(node_path, "datamap.zz9")
    if remote:
        with open(datamap_path + ".lz4", "rb") as f:
            data = lz4lib.lz4framed.decompress(f.read())
    else:
        with open(datamap_path, "rb") as f:
            data = f.read()
    m = json.loads(data)
    num_changes = 0
    for k in list(m.keys()):
        if k.startswith("/__batch_"):
            num_changes += 1
            if args["--dry-run"]:
                continue
            del m[k]
    if not args["--dry-run"] and num_changes > 0:
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


def quick_dirty_fix_datamaps_for_dataset(args, store, ds_id):
    """
    This is "quick and dirty" because it does its work outside of a factory.
    Make sure no one is using the dataset!
    Return num_changes
    """
    num_local_changes = 0
    num_remote_changes = 0
    node_ids = list_nodes(store, ds_id)
    for node_id in node_ids:
        address = {"dataset": ds_id, "node": node_id}
        local_node_path = store.local_node_path(address)
        if os.path.exists(local_node_path):
            n = _quick_dirty_fix_datamap(args, local_node_path, remote=False)
            if n > 0:
                num_local_changes += 1
        remote_node_path = store.repo_node_path(address)
        n = _quick_dirty_fix_datamap(args, remote_node_path, remote=True)
        if n > 0:
            num_remote_changes += 1
    print(
        "dataset:",
        ds_id,
        "num_nodes:",
        len(node_ids),
        "num_local_changes:",
        num_local_changes,
        "num_remote_changes:",
        num_remote_changes,
    )
    return num_local_changes + num_remote_changes


def main():
    args = docopt.docopt(__doc__)
    if args["--from-file"]:
        with open(args["<dataset-ids-file>"]) as f:
            ds_ids = f.read().split()
    else:
        ds_ids = [args["<dataset-id>"]]
    if not args["--quick-dirty"]:
        raise NotImplementedError("Sorry, safe datamap fixing not yet available.")
    store = create_store(args)
    num_changed_datasets = 0
    for ds_id in ds_ids:
        n = quick_dirty_fix_datamaps_for_dataset(args, store, ds_id)
        if n > 0:
            num_changed_datasets += 1
    print("num_datasets:", len(ds_ids), "num_changed_datasets:", num_changed_datasets)
    if args["--dry-run"]:
        print("Dry run, no actual changes made.")


if __name__ == "__main__":
    sys.exit(main())
