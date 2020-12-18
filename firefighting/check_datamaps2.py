#!/var/lib/crunch.io/venv/bin/python
"""
Check datamaps for consistency with variants and data files - version 2

Example:
    check_datamaps.py e47e3008ae17410aa285a757b5346efd --node-id=__tip000__

The difference between this script and the previous check_datamaps.py script
is that this one imports and uses the zz9d datamap consistency checking code
that was written after the original check_datamaps.py script.
"""
from __future__ import print_function
import argparse
import errno
import json
import os
import sys

import lz4framed

from zz9d.stores.datamaps import Datamap
from zz9d.stores.simplefs_4 import SimpleFileSystemStore

try:
    input = raw_input  # PY2 compatibility
except NameError:
    pass


class DatamapCheckError(Exception):
    pass


def dprintf(args_, fmt, *args, **kwargs):
    if args_.oneline:
        return
    print(fmt.format(*args, **kwargs))
    sys.stdout.flush()


def eprintf(args_, fmt, *args, **kwargs):
    msg = fmt.format(*args, **kwargs)
    if args_.raise_on_error:
        raise DatamapCheckError(msg)
    if args_.oneline:
        return
    print("ERROR: {}".format(msg))
    sys.stdout.flush()


def load_datamap(args, store, ds_id, node_id):
    """
    Return an initialized Datamap object ready for use.

    We're not using zz9d.stores.simplefs_4.SimpleFilesSystemStore.load_datamap()
    because we want to avoid downloads and local file writes.
    """
    if not isinstance(store, SimpleFileSystemStore):
        raise TypeError("store: expected SimpleFileSystemStore")
    address = {"dataset": ds_id}
    local_ds_dir = store.local_root_path(address)
    repo_ds_dir = store.repo_root_path(address)

    datamap_dict = None
    for ds_dir, local in ((local_ds_dir, True), (repo_ds_dir, False)):
        suffix = "" if local else ".lz4"
        full_path = "{}/versions/{}/datamap.zz9{}".format(ds_dir, node_id, suffix)
        if not os.path.exists(full_path):
            continue
        dprintf(args, "Loading {}", full_path)
        if local:
            with open(full_path) as f:
                datamap_dict = json.load(f)
                break
        with open(full_path) as f:
            data = lz4framed.decompress(f.read())
            datamap_dict = json.loads(data)
            break
    if not datamap_dict:
        eprintf(args, "No datamap for node {}: {}", node_id, full_path)
        return None

    datamap = Datamap(
        "{}/datafiles".format(local_ds_dir),
        "{}/datafiles".format(repo_ds_dir),
        datamap_dict,
        store,
    )
    return datamap


def check_datamaps(args, ds_id):  # noqa: C901
    """
    Check the datamaps for the dataset with ID ds_id
    Return None if the node doesn't exist, otherwise
    return the number of nodes that had errors
    """
    address = {"dataset": ds_id}
    store = SimpleFileSystemStore(
        datadir=args.datadir, repodir=args.repodir, tmpdir=args.tmpdir
    )
    if args.node_id:
        node_ids = [args.node_id]
    else:
        repo_ds_dir = store.repo_root_path(address)
        try:
            node_ids = os.listdir(repo_ds_dir + "/versions")
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise
            if args.oneline:
                print("{}@:DELETED".format(ds_id))
                sys.stdout.flush()
            else:
                dprintf(args, "Dataset {} does not exist", ds_id)
            return None
    dprintf(
        args,
        "Checking {} datamaps for dataset {}\n",
        len(node_ids),
        ds_id,
    )
    result = {}
    for node_id in sorted(node_ids):
        try:
            result[node_id] = check_datamap(args, store, ds_id, node_id)
        except Exception as err:
            if args.raise_on_error:
                raise
            result[node_id] = err
    if args.oneline:
        nodes_with_errors = _print_oneline_summary(ds_id, result)
    else:
        nodes_with_errors = _print_summary(ds_id, result)
    sys.stdout.flush()
    return nodes_with_errors


def _print_oneline_summary(ds_id, result):
    nodes_with_errors = 0
    err = None
    for node_id in sorted(result):
        status = result[node_id]
        if isinstance(status, int) and status == 0:
            print("{}@{}:OK".format(ds_id, node_id))
            sys.stdout.flush()
            continue
        nodes_with_errors += 1
        if isinstance(status, int):
            if status > 0:
                print(
                    "{}@{}:ERROR {} columns with errors".format(ds_id, node_id, status)
                )
            else:
                print("{}@{}:ERROR Code {}".format(ds_id, node_id, status))
        elif isinstance(status, Exception) and err is None:
            err = status
            print(
                "{}@{}:ERROR {}: {}".format(ds_id, node_id, err.__class__.__name__, err)
            )
        else:
            print("{}@{}:ERROR {}".format(ds_id, node_id, status))
        sys.stdout.flush()
    return nodes_with_errors


def _print_summary(ds_id, result):
    print()
    print("Dataset {} health:".format(ds_id))
    nodes_with_errors = 0
    for node_id in sorted(result):
        status = result[node_id]
        is_ok, status_message = _format_status(status)
        if not is_ok:
            nodes_with_errors += 1
        print("  {:14}: {}".format(node_id, status_message))
    print("{} nodes with errors".format(nodes_with_errors))
    print()
    return nodes_with_errors


def _format_status(status):
    """Return is_ok, status_message)"""
    if isinstance(status, int):
        if status == 0:
            return (True, "No errors")
        elif status > 0:
            return (False, "{} columns with errors".format(status))
        else:
            return (False, "Error code {}".format(status))
    elif isinstance(status, Exception):
        err = status
        return (False, "{}: {}".format(err.__class__.__name__, err))
    else:
        return (False, "Unknown error ({})".format(status))


def check_datamap(args, store, ds_id, node_id):
    """
    Return the status of this datamap node:
    0 if no columns had errors
    n > 0 if n columns had errors
    < 0 if there was some other major error
    """
    datamap = load_datamap(args, store, ds_id, node_id)
    if not datamap:
        # Could not load datamap for this node
        return -101
    result = datamap.consistency_check(ds_id, check_column_files=args.columns)
    for item in result:
        dprintf(args, "Error: {}", item)
    return len(result)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "ds_id_or_filename",
        metavar="<dataset-id-or-filename>",
        help="Dataset ID or file containing IDs",
    )
    parser.add_argument(
        "--fromfile", action="store_true", help="Treat parameter as filename not ID"
    )
    parser.add_argument(
        "--start-line",
        metavar="N",
        type=int,
        help="Starting 1-based line number (only used with --fromfile)",
    )
    parser.add_argument(
        "--node-id", metavar="<node-id>", help="Node/Version ID, default is all nodes"
    )
    parser.add_argument(
        "--oneline", action="store_true", help="Only output line line per dataset"
    )
    parser.add_argument(
        "--columns", action="store_true", help="Check column file consistency"
    )
    parser.add_argument(
        "--raise-on-error",
        action="store_true",
        help="Raise DatamapCheckError instead of printing message",
    )
    parser.add_argument("--datadir", default="/var/local/fake_zz9data")
    parser.add_argument("--repodir", default="/var/lib/crunch.io/zz9repo")
    parser.add_argument("--tmpdir", default="/var/local/fake_zz9tmp")
    args = parser.parse_args()

    if args.fromfile:
        nodes_with_errors = 0
        start_line = args.start_line if args.start_line is not None else 0
        with open(args.ds_id_or_filename) as f:
            for line_num, line in enumerate(f, 1):
                if line_num < start_line:
                    continue
                ds_id = line.strip()
                if not ds_id:
                    continue
                result = check_datamaps(args, ds_id)
                if result is not None:
                    nodes_with_errors += result
    else:
        nodes_with_errors = check_datamaps(args, args.ds_id_or_filename)
    return 0 if nodes_with_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
