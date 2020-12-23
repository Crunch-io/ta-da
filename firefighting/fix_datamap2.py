#!/var/lib/crunch.io/venv/bin/python
"""
Perform limited repairs directly on a datamap in EFS

This script can repair a column in a datamap if:
- It is a text column AND
- It has extra paths in the datamap OR
- It has paths missing from the datamap but present in the repo

If running this script in --stream mode, messages will be received via the "send" file
and replies posted via the "done" file. On the other end, the drive_fix_datamap.py
script writes to the send file and reads from the done file. See that script for
details.

Before running this script, you should:

- Make the dataset unavailable via "Maintenance" link in superadmin
- From cr.shell run ds.retire() to cleanup/sync, release, etc.

If this script is run in --stream mode then drive_fix_datamap.py will do these things
for you.
"""
from __future__ import print_function
import argparse
import os
import json
import re
import shutil
import sys
import tempfile
import time
import traceback

import lz4framed
import six

from zz9d.stores.simplefs_4 import SimpleFileSystemStore

from check_datamaps2 import load_datamap

SEND_PATTERN = re.compile(r"^(?P<timestamp>\S+)\s+(?P<ds_id>\w+)@(?P<node_id>[^:]+)$")
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

try:
    input = raw_input  # PY2 compatibility
except NameError:
    pass


class DoesNotNeedRepair(Exception):
    pass


class CannotRepair(Exception):
    pass


def fix_datamap(args):
    if not args.yes:
        print("***** DANGEROUS - this script modifies a datamap in EFS directly.")
        if args.dry_run:
            print("(Fortunately, this is just a *dry run*, no files will be changed.)")
        print()
        print("Before running this script, you should:")
        print('- Make this dataset unavailable via "Maintenance" link in superadmin')
        print("- From cr.shell run ds.retire() to cleanup/sync, release, etc.")
        print()
        sys.stdout.flush()
        answer = input("Are you ready to proceed? [y/N]: ")
        if answer.strip().lower()[:1] != "y":
            print("Canceling the operation.")
            return 1
    ds_id = args.ds_id
    node_id = args.node_id
    var_ids = args.var_ids if args.var_ids else None
    try:
        if not ds_id:
            raise ValueError("<dataset-id> is required if not in --stream mode")
        if not node_id:
            raise ValueError("<node-id> is required if not in --stream mode")
        repairer = DatamapRepairer(args, ds_id, node_id, var_ids)
        rc = repairer.fix_datamap()
    except DoesNotNeedRepair as exc:
        print(exc)
        rc = 0
    except CannotRepair as exc:
        print(exc)
        rc = 1
    except Exception:
        traceback.print_exc()
        rc = 1
    except KeyboardInterrupt:
        print("\nStopped.")
        rc = 1
    if rc == 0:
        print()
        dry_run_str = " (dry run)" if args.dry_run else ""
        print("The datamap repair appears to have succeeded{}".format(dry_run_str))
        print("Remember to make the dataset available again in superadmin.")
    else:
        print()
        print("There appears to have been a problem.")
        print("This script will exit with code {}".format(rc))
        print("Good luck.")
    sys.stdout.flush()
    return rc


class DatamapRepairer(object):
    """
    Fix datamaps for the dataset, node, and variables.
    """

    def __init__(self, args, ds_id, node_id, var_ids):
        self.args = args
        self.ds_id = ds_id
        self.node_id = node_id
        self.var_ids = var_ids

        #
        # Load up data used by many methods
        #

        store = SimpleFileSystemStore(
            datadir=args.datadir, repodir=args.repodir, tmpdir=args.tmpdir
        )
        self.datamap = datamap = load_datamap(args, store, ds_id, node_id)
        frame_id = "primary"
        frame_info = _load_frame_info(datamap, frame_id)
        self.numrows = frame_info["numrows"]
        self.frame_vardef = frame_vardef = {frame_id: datamap._load_vardef(frame_id)}

        self.datamap_items_to_test = datamap_items_to_test = {
            "%s%s" % (variant, f)
            for f, variant in datamap.map.items()
            if f.startswith("/primary")
        }

        # column_data_files = {
        #    filename
        #    for filename in datamap_items_to_test
        #    if ".data.zz9" in filename and "__batch_id__" not in filename
        # }

        self.var_extensions = var_extensions = {}
        for filename in datamap_items_to_test:
            # Build dictionary with {root_path: [list_extensions] to easily
            # find files for a variable that should not be there.
            root_var, extension = filename.split(".", 1)
            extension = "." + extension
            if root_var in var_extensions:
                var_extensions[root_var].append(extension)
            else:
                var_extensions[root_var] = [extension]

        if var_ids is None:
            self.var_ids = [
                var_id
                for (var_id, var_def) in six.iteritems(frame_vardef[frame_id])
                if var_def.get("type", {}).get("class") == "text"
            ]
        else:
            for var_id in var_ids:
                if var_id not in frame_vardef:
                    raise CannotRepair("{} is not a valid variable ID".format(var_id))
                classname = frame_vardef[var_id].get("type", {}).get("class")
                if classname != "text":
                    raise CannotRepair(
                        "Column {} is class '{}'. Can only repair text".format(
                            var_id, classname
                        )
                    )

    def fix_datamap(self):
        """
        Return 0 if everything is Ok, else raise an exception:
            CannotRepair if there is a problem that can't be repaired
            DoesNotNeedRepair if everything looks Ok
        """
        prev_dm = self.datamap.map.copy()
        dm = self._repair_datamap()
        if not dm:
            # Avoid wiping out the Datamap accidentally
            raise RuntimeError("Replacement datamap is empty, aborting")

        if prev_dm == dm:
            raise DoesNotNeedRepair("No change to datamap")

        if not self.args.dry_run:
            self._replace_datamap(dm)

        return 0

    def _repair_datamap(self):
        """
        Repair the datamap in-memory and return the modified datamap dictionary.
        Raise CannotRepair if the datamap cannot be repaired for any reason.
        var_ids: List of variables to repair, or all text variables if None
        """
        num_ok_vars = 0
        var_ids = self.var_ids
        for var_id in var_ids:
            try:
                self._repair_column(var_id)
            except DoesNotNeedRepair as exc:
                print(exc)
                num_ok_vars += 1
            sys.stdout.flush()

        if num_ok_vars == len(var_ids):
            raise DoesNotNeedRepair(
                "All {} text variables were Ok".format(len(var_ids))
            )

        return self.datamap.map.copy()

    def _repair_column(self, var_id):  # noqa: C901
        """
        var_id: ID of column to be repaired
        """
        data_path, data_variant, structure_type, shape = self._check_data_path(var_id)

        # All filename extensions including the always-required .data.zz9
        expected_file_extensions = self.datamap.column_extension_map[structure_type]
        expected_paths = [
            "/primary/{}.{}".format(var_id, extension)
            for extension in expected_file_extensions
        ]

        # Make sure each of the required paths exists on disk in the correct variant
        for expected_path in expected_paths:
            cur_variant = self.datamap.map.get(expected_path)
            if cur_variant:
                path_exists_on_disk = self._path_exists(expected_path)
            else:
                path_exists_on_disk = self._path_exists(
                    expected_path, variant=data_variant
                )
            if not path_exists_on_disk:
                if cur_variant:
                    expected_variant_str = " in variant {}".format(cur_variant)
                else:
                    expected_variant_str = ""
                raise CannotRepair(
                    "Expected path {} for variable {} does not exist on disk{}".format(
                        expected_path, var_id, expected_variant_str
                    )
                )
            elif cur_variant and cur_variant != data_variant:
                raise CannotRepair(
                    "Expected path {} for variable {} is in variant {} not {}".format(
                        expected_path, var_id, cur_variant, data_variant
                    )
                )

        # Make list of paths that exist in the datamap but should not be there
        paths_to_del = []
        var_path_prefix = "{}.".format(var_id)
        for path in self.datamap.map:
            if not path.startswith(var_path_prefix):
                continue
            if path not in expected_paths:
                paths_to_del.append(path)

        # Make list of required paths that exist on disk but not yet in datamap
        paths_to_add = [path for path in expected_paths if path not in self.datamap.map]

        if (not paths_to_del) and (not paths_to_add):
            raise DoesNotNeedRepair(
                "Variable {} has all required paths and no extra paths".format(var_id)
            )

        # Remove every path for this variable from the datamap that should not be there
        for path in paths_to_del:
            del self.datamap.map[path]

        # Add every path that was missing from the datamap but exists on disk
        # NOTE: We previously checked that the file variant is equal to the data variant
        for path in paths_to_add:
            self.datamap.map[path] = data_variant

        print(
            "INFO: Variable {} repaired: removed {}, added {}".format(
                paths_to_del, paths_to_add
            )
        )
        sys.stdout.flush()

    def _path_exists(self, path, variant=None):
        """
        Return true iff a datafile exists for the given datamap path.
        Checks local disk first then EFS. Does not download.
        If variant is None, check the in variant currently in the datamap.
        Otherwise, temporarily set or override the datamap variant.
        """
        cur_variant = self.datamap.map.get(path)
        if not cur_variant and not variant:
            # We don't have a variant to check. Assume it doesn't exist.
            return False
        if variant and cur_variant != variant:
            # Temporarily set or override datamap entry
            self.datamap.map[path] = variant
        try:
            try:
                self.datamap.read_without_fetch(path).close()
            except IOError:
                return False
            else:
                return True
        finally:
            # Restore datamap if it was temporarily changed
            if variant and cur_variant != variant:
                if cur_variant:
                    self.datamap.map[path] = cur_variant
                else:
                    del self.datamap.map[path]

    def _check_data_path(self, var_id):  # noqa: C901
        """
        Raise DoesNotNeedRepair if this column is OK
        Raise CannotRepair if the data file is such that this column can't be repaired
        Otherwise, if this is a potentially repairable broken text column, return:
            (data_path, data_variant, structure_type, shape)
        structure_type: structure of variable from datamap.find_column_structure_type()
        shape: tuple if data file in numpy format, else None
        """
        frame_id = "primary"
        var_file_name = "{}.data.zz9".format(var_id)  # as found in datamap, no .lz4
        data_path = "/{}/{}".format(frame_id, var_file_name)
        data_variant = self.datamap.map.get(data_path)
        if not data_variant:
            raise CannotRepair(
                "{} does not exist in the node {} datamap".format(
                    data_path, self.node_id
                )
            )

        column_data_file = "{}/{}".format(data_variant, data_path)
        check_column_args = (
            column_data_file,
            self.var_extensions,
            self.datamap_items_to_test,
            self.frame_vardef,
        )
        errors = self.datamap._check_column_data(check_column_args)
        if not errors:
            raise DoesNotNeedRepair("Column {} is OK".format(var_id))

        # structure_type is one of:
        # - 'structured'
        # - 'coded text'
        # - 'categorical'
        # - 'indexed'
        # - 'scalar'
        # - 'indexed text'
        # - 'cardinal'
        # - 'unstructured'
        #
        # shape is None iff the column data file was not in numpy format
        try:
            structure_type, shape = self.datamap.find_column_structure_type(
                frame_id, var_file_name, self.frame_vardef[frame_id]
            )
        except IOError:
            raise CannotRepair(
                "{} data file does not exist in the repo in variant {}".format(
                    data_path, data_variant
                )
            )

        if shape is not None:
            if shape[0] != self.numrows:
                raise CannotRepair(
                    "Variable {} in node {}: "
                    "length {} does not match existing length {}".format(
                        var_id, self.node_id, shape[0], self.numrows
                    )
                )

        if structure_type != "indexed text" and shape is None:
            raise CannotRepair(
                "Column {} is in unexpected {} format and has error: {}".format(
                    var_id, structure_type, errors
                )
            )

        var_info = self.frame_vardef[frame_id].get(var_id)
        if not var_info:
            raise CannotRepair(
                "Variable {} in node {}: not in the variables metadata".format(
                    var_id, self.node_id
                )
            )
        classname = var_info.get("type", {}).get("class")
        if classname != "text":
            raise CannotRepair("Column {} is not a text variable".format(var_id))

        return (data_path, data_variant, structure_type, shape)

    def _replace_datamap(self, dm):
        ds_dir = self._get_ds_repo_dir()
        full_path = "{}/versions/{}/datamap.zz9.lz4".format(ds_dir, self.node_id)
        basename = os.path.basename(full_path)
        dirname = os.path.dirname(full_path)
        # Back up the current datamap file to datamap.zz9.lz4.bakXXX
        with open(full_path, "rb") as f_orig:
            with tempfile.NamedTemporaryFile(
                prefix=basename + ".bak", dir=dirname, delete=False
            ) as f_bak:
                print("Backing up {} to {}".format(f_orig.name, f_bak.name))
                sys.stdout.flush()
                shutil.copyfileobj(f_orig, f_bak)
                shutil.copystat(f_orig.name, f_bak.name)
        # Save/compress the modified datamap to datamap.zz9.lz4.tmpXXX
        dm_compressed_bytes = lz4framed.compress(json.dumps(dm).encode("utf-8"))
        with tempfile.NamedTemporaryFile(
            prefix=basename + ".tmp", dir=dirname, delete=False
        ) as f_tmp:
            print("Writing modified datamap to {}".format(f_tmp.name))
            sys.stdout.flush()
            f_tmp.write(dm_compressed_bytes)
        # Atomic rename datamap.zz9.lz4.tmpXXX to datamap.zz9.lz4
        print("Renaming {} to {}".format(f_tmp.name, full_path))
        sys.stdout.flush()
        os.rename(f_tmp.name, full_path)

    def _get_ds_repo_dir(self):
        prefix = self.ds_id[:2]
        return "{}/{}/{}".format(self.args.repodir, prefix, self.ds_id)


def stream_fix_datamaps(args):
    try:
        if not args.send_file:
            raise ValueError("Cannot run --stream mode without --send-file")
        if not args.done_file:
            raise ValueError("Cannot run --stream mode without --done-file")
        _run_stream_fix_datamaps(args, args.send_file, args.done_file)
    except KeyboardInterrupt:
        print("\nStopped")
        sys.stdout.flush()
        return 0
    except Exception:
        traceback.print_exc()
        return 1


def _run_stream_fix_datamaps(args, send_filename, done_filename):
    with open(send_filename) as send_f:
        with open(done_filename, "a") as done_f:
            while True:
                line = send_f.readline()
                if not line:
                    # EOF, keep waiting for next line
                    time.sleep(0.25)
                    continue
                line = line.strip()
                print("Received: {}".format(line))
                sys.stdout.flush()
                m = SEND_PATTERN.match(line)
                if not m:
                    raise ValueError(
                        "Line in send file not in right format: {}".format(line)
                    )
                timestamp = m.group("timestamp")
                ds_id = m.group("ds_id")
                node_id = m.group("node_id")
                var_ids = None
                try:
                    repairer = DatamapRepairer(args, ds_id, node_id, var_ids)
                    repairer.fix_datamap()
                    status = "OK"
                except DoesNotNeedRepair as exc:
                    status = "DoesNotNeedRepair:{}".format(exc)
                except CannotRepair as exc:
                    status = "CannotRepair:{}".format(exc)
                except Exception as exc:
                    status = "ERROR:{}:{}".format(exc.__class__.__name__, exc)
                except KeyboardInterrupt:
                    status = "STOP"
                msg = "{} {}@{}:{}\n".format(timestamp, ds_id, node_id, status)
                done_f.write(msg)
                done_f.flush()
                os.fdatasync(done_f.fileno())
                print("Sent    : {}".format(status))
                sys.stdout.flush()
                if status == "STOP":
                    raise KeyboardInterrupt()


def _load_frame_info(datamap, frame_id):
    frame_info_path = "/{}/frame.zz9".format(frame_id)
    with datamap.read_without_fetch(frame_info_path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("ds_id", metavar="<dataset-id>", nargs="?", help="Dataset ID")
    parser.add_argument("node_id", metavar="<node-id>", nargs="?", help="Node ID")
    parser.add_argument(
        "var_ids", metavar="<variable-id>", nargs="*", help="Variable ID"
    )
    parser.add_argument("--dry-run", action="store_true", help="Don't change files")
    parser.add_argument("--yes", action="store_true", help='No "Are you sure?" prompt')
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Streaming mode: read from send file, append to done file",
    )
    parser.add_argument("--send-file", help="Send file (read), only used by --stream")
    parser.add_argument("--done-file", help="Done file (append), only used by --stream")
    parser.add_argument("--datadir", default="/var/local/fake_zz9data")
    parser.add_argument("--repodir", default="/var/lib/crunch.io/zz9repo")
    parser.add_argument("--tmpdir", default="/var/local/fake_zz9tmp")
    args = parser.parse_args()
    # Set attributes required by functions imported from check_datamaps
    args.local = False
    args.oneline = False
    args.raise_on_error = True
    if args.stream:
        return stream_fix_datamaps(args)
    else:
        return fix_datamap(args)


if __name__ == "__main__":
    sys.exit(main())
