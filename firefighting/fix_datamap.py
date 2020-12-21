#!/var/lib/crunch.io/venv/bin/python
"""
Perform limited repairs directly on a datamap in EFS

This script can repair a column in a datamap if:
- It is a text column
- It is in INDX or coded text format
- The .buffer.zz9 file for the column exists in the repo but not in the datamap

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

from check_datamaps import (
    check_column,
    check_path,
    DatamapCheckError,
    get_ds_dir,
    load_datamap,
    load_frame,
    load_variables,
    open_datafile,
    path_file_exists,
    read_numpy_header_after_4,
)

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
        rc = _fix_datamap(args, ds_id, node_id, var_ids)
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


def _fix_datamap(args, ds_id, node_id, var_ids):
    """
    Fix datamaps for the dataset, node, and variables.
    Return 0 if everything is Ok, else raise an exception:
        CannotRepair if there is a problem that can't be repaired
        DoesNotNeedRepair if everything looks Ok
    """
    dm = _repair_datamap(args, ds_id, node_id, var_ids)
    assert dm

    if not args.dry_run:
        _replace_datamap(args, ds_id, node_id, dm)

    return 0


def _repair_datamap(args, ds_id, node_id, var_ids):
    """
    Repair the datamap in-memory and return the modified datamap dictionary.
    Raise CannotRepair if the datamap cannot be repaired for any reason.
    var_ids: List of variables to repair, or all text variables if None
    """
    dm = load_datamap(args, ds_id, node_id, local=False)
    frame = load_frame(args, ds_id, dm)
    numrows = frame["numrows"]
    variables = load_variables(args, ds_id, dm)

    if var_ids is None:
        var_ids = [
            var_id
            for (var_id, var_def) in six.iteritems(variables)
            if var_def.get("type", {}).get("class") == "text"
        ]
    else:
        for var_id in var_ids:
            if var_id not in variables:
                raise CannotRepair("{} is not a valid variable ID".format(var_id))
            classname = variables[var_id].get("type", {}).get("class")
            if classname != "text":
                raise CannotRepair(
                    "Column {} is class '{}'. This script can only repair text".format(
                        var_id, classname
                    )
                )

    num_ok_vars = 0
    for var_id in var_ids:
        try:
            _repair_text_column(args, ds_id, node_id, var_id, dm, variables, numrows)
        except DoesNotNeedRepair as exc:
            print(exc)
            num_ok_vars += 1
        sys.stdout.flush()

    if num_ok_vars == len(var_ids):
        raise DoesNotNeedRepair("All {} text variables were Ok".format(len(var_ids)))

    return dm


def _repair_text_column(  # noqa: C901
    args, ds_id, node_id, var_id, dm, variables, numrows
):
    """
    var_id: ID of text column to be repaired
    dm: Datamap dictionary
    """
    data_path, data_variant = _check_data_path(
        args, ds_id, node_id, var_id, dm, variables, numrows
    )

    buffer_path = "/primary/{}.buffer.zz9".format(var_id)
    buffer_variant = dm.get(buffer_path)
    if buffer_variant:
        buffer_file_exists = path_file_exists(
            args, ds_id, buffer_variant, buffer_path, local=False
        )
    else:
        buffer_file_exists = path_file_exists(
            args, ds_id, data_variant, buffer_path, local=False
        )
    if buffer_variant == data_variant and buffer_file_exists:
        raise DoesNotNeedRepair(
            "Nothing to repair- {} is in the datamap and in the repo"
            " in data variant {}".format(buffer_path, data_variant)
        )
    elif buffer_variant is not None and buffer_file_exists:
        raise CannotRepair(
            "{} exists in the datamap and repo but is in variant {},"
            " not in data variant {}".format(buffer_path, buffer_variant, data_variant)
        )
    elif not buffer_file_exists:
        raise CannotRepair(
            "{} buffer file does not exist in the repo"
            " in data variant {}".format(buffer_path, data_variant)
        )

    # Remove every key for this variable from the datamap except the .data.zz9 one
    non_data_keys = [
        k for k in sorted(dm) if (k.startswith(var_id + ".") and k != data_path)
    ]
    for non_data_key in non_data_keys:
        print("Deleting extra key for column {}: {}".format(var_id, non_data_key))
        del dm[non_data_key]

    # Set the variant for the buffer file
    dm[buffer_path] = data_variant

    # Sanity check
    f = open_datafile(args, ds_id, dm, buffer_path)
    if f is None:
        raise CannotRepair(
            "BUG - after repair, {} does not exist in the repo and/or datamap"
            " in data variant {}".format(buffer_path, data_variant)
        )
    with f:
        b4 = f.read(4)
    print(
        "INFO: path {} is set up in variant {}"
        " and has structure '{}'".format(buffer_path, data_variant, b4)
    )
    sys.stdout.flush()


def _check_data_path(  # noqa: C901
    args, ds_id, node_id, var_id, dm, variables, numrows
):
    """
    Raise CannotRepair if the data file is such that this column can't be repaired
    Raise DoesNotNeedRepair if this column is OK
    return (data_path, data_variant) if this is a repairable broken text column.
    """
    data_path = "/primary/{}.data.zz9".format(var_id)
    data_variant = dm.get(data_path)
    if not data_variant:
        raise CannotRepair(
            "{} does not exist in the node {} datamap".format(data_path, node_id)
        )

    check_result = "(unknown error)"
    try:
        if check_column(args, ds_id, dm, variables, numrows, data_path):
            raise DoesNotNeedRepair("Column {} is OK".format(var_id))
    except DatamapCheckError as err:
        check_result = err

    f = open_datafile(args, ds_id, dm, data_path)
    if f is None:
        raise CannotRepair(
            "{} data file does not exist in the repo"
            " in variant {}".format(data_path, data_variant)
        )
    with f:
        b4 = f.read(4)

        if b4 not in (b"INDX", b"\x93NUM"):
            raise CannotRepair(
                "Column {} is in unexpected {} format and has error: {}".format(
                    var_id, b4, check_result
                )
            )

        if b4 == b"\x93NUM":
            header = read_numpy_header_after_4(f)
            if header is None:
                raise CannotRepair(
                    "Column {}: numpy data file could not be loaded".format(var_id)
                )
            shape, _, dtype = header
            if shape[0] != numrows:
                raise CannotRepair(
                    "Column {}: numpy data"
                    " length {} does not match existing length {}".format(
                        var_id, shape[0], numrows
                    )
                )
            if "U" in dtype.str or "S" in dtype.str:
                # Old "structured" format. There should *not*
                # be any "S" but csv_import used to write them.
                missing_path = "/primary/{}.missing.zz9".format(var_id)
                try:
                    check_path(args, ds_id, dm, data_path, "text", missing_path)
                    raise AssertionError(
                        "Column {}: text column in old structured format is OK"
                        " so check_column() call should have succeeded earlier".format(
                            var_id
                        )
                    )
                except DatamapCheckError as err:
                    raise CannotRepair(
                        "Column {}: text column in old structured format: {}".format(
                            var_id, err
                        )
                    )
            else:
                # New "coded text" format
                buffer_path = "/primary/{}.buffer.zz9".format(var_id)
                try:
                    check_path(args, ds_id, dm, data_path, "text", buffer_path)
                    raise AssertionError(
                        "Column {}: text column in coded text format is OK"
                        " so check_column() call should have succeeded earlier".format(
                            var_id
                        )
                    )
                except DatamapCheckError:
                    pass  # we possibly can repair this

    return (data_path, data_variant)


def _replace_datamap(args, ds_id, node_id, dm):
    ds_dir = get_ds_dir(args, ds_id, local=False)
    full_path = "{}/versions/{}/datamap.zz9.lz4".format(ds_dir, node_id)
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
                    _fix_datamap(args, ds_id, node_id, var_ids)
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
