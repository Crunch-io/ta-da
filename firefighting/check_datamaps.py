#!/var/lib/crunch.io/venv/bin/python
"""
Check datamaps for consistency with variants and data files

Example:
    check_datamaps.py e47e3008ae17410aa285a757b5346efd --node-id=__tip000__

NOTE: This script is imported as a module by fix_datamap !!!
"""
from __future__ import print_function
import argparse
import json
import marshal
import os
import struct
import sys

import lz4framed
import numpy as np
import six

from zz9d.objects.dictionaries import odict
from zz9d.stores.datamaps import CARDINAL_MAGIC, MUD, SCALAR_MAGIC
from zz9d.stores.indexedio import IndexedIO

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


class Lz4Reader(object):
    """LZ4 decompressor with API of a file-like object open for binary read"""

    def __init__(self, f):
        """f: file opened for binary read"""
        self.f = f
        self.buf = b""
        self.decompressor = iter(lz4framed.Decompressor(f))

    def read(self, size=None):
        if self.f.closed:
            raise ValueError("I/O operation on closed file")
        if size is None or size < 0:
            return self._read_all()
        result = []
        result_size = 0
        while result_size < size:
            needed = size - result_size
            if len(self.buf) >= needed:
                result.append(self.buf[:needed])
                result_size += len(result[-1])
                self.buf = self.buf[needed:]
                continue
            try:
                self.buf += next(self.decompressor)
            except StopIteration:
                result.append(self.buf)
                result_size += len(result[-1])
                self.buf = b""
                break
        return b"".join(result)

    def _read_all(self):
        result = [self.buf]
        self.buf = b""
        for chunk in self.decompressor:
            result.append(chunk)
        return b"".join(result)

    def close(self):
        self.f.close()
        self.buf = b""
        self.decompressor = None

    @property
    def closed(self):
        return self.f.closed

    @property
    def name(self):
        return self.f.name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __iter__(self):
        return LineIterator(self)


class LineIterator(object):
    def __init__(self, f):
        """f: file-like object opened for binary read"""
        self.f = f
        self.buf = b""

    def __iter__(self):
        return self

    def __next__(self):
        result = []
        while self.f is not None:
            i = self.buf.find(b"\n")
            if i >= 0:
                # Found end-of-line
                result.append(self.buf[: i + 1])
                self.buf = self.buf[i + 1 :]
                break
            elif self.buf:
                result.append(self.buf)
            self.buf = self.f.read(1024)
            if not self.buf:
                # end-of-file
                self.f = None
        if result:
            return b"".join(result)
        raise StopIteration()

    next = __next__  # PY2 compatibility


def get_ds_dir(ds_id, local=False):
    if local:
        return "/var/lib/crunch.io/zz9data/hot/" + ds_id[:2] + "/" + ds_id
    else:
        return "/var/lib/crunch.io/zz9repo/" + ds_id[:2] + "/" + ds_id


def load_datamap(args, ds_id, node_id, local=False):
    """
    Return dict, or None if datamap doesn't exist
    """
    ds_dir = get_ds_dir(ds_id, local=local)
    suffix = "" if local else ".lz4"
    full_path = "{}/versions/{}/datamap.zz9{}".format(ds_dir, node_id, suffix)
    if not os.path.exists(full_path):
        eprintf(args, "No datamap for node {}: {}", node_id, full_path)
        sys.stdout.flush()
        return None
    dprintf(args, "Loading {}", full_path)
    sys.stdout.flush()
    if local:
        with open(full_path) as f:
            return json.load(f)
    with open(full_path) as f:
        data = lz4framed.decompress(f.read())
        return json.loads(data)


def open_datafile(args, ds_id, dm, path):
    """
    dm: Datamap dictionary
    path: Path key to be looked up in datamap dict
    Return open file object, or None if file not found or not in datamap
    """
    variant = dm.get(path)
    if not path:
        return None  # No frame.zz9 in the datamap, it's an error
    ds_dir = get_ds_dir(ds_id, local=args.local)
    suffix = "" if args.local else ".lz4"
    full_path = "{}/datafiles/{}/{}{}".format(ds_dir, variant, path, suffix)
    try:
        f = open(full_path, "rb")
    except IOError:
        return None
    if not args.local:
        f = Lz4Reader(f)
    return f


def load_frame(args, ds_id, dm):
    """
    Load the frame.zz9 file
    dm: Datamap dictionary
    Return dictionary containing contents of frame.zz9, or None if it can't be opened.
    """
    f = open_datafile(args, ds_id, dm, "/primary/frame.zz9")
    if f is None:
        return None
    with f:
        return json.load(f)


def load_variables(args, ds_id, dm):
    """
    dm: Datamap dictionary
    Return dictionary mapping variable ID to variable definition
    Return None if no variables.zz9 file exists
    """
    f = open_datafile(args, ds_id, dm, "/primary/variables.zz9")
    if f is None:
        return None
    with f:
        result = odict()
        MUD(f).load(result)
        return result.lookup


def variant_dir_exists(ds_id, variant, local=False):
    ds_dir = get_ds_dir(ds_id, local=local)
    variant_dir = "{}/datafiles/{}".format(ds_dir, variant)
    if os.path.isdir(variant_dir):
        return True
    if local:
        # Also check repo dir
        repo_ds_dir = get_ds_dir(ds_id, local=False)
        repo_variant_dir = "{}/datafiles/{}".format(repo_ds_dir, variant)
        if os.path.isdir(repo_variant_dir):
            return True
    return False


def path_file_exists(ds_id, variant, path, local=False):
    ds_dir = get_ds_dir(ds_id, local=local)
    suffix = "" if local else ".lz4"
    variant_dir = "{}/datafiles/{}".format(ds_dir, variant)
    full_path = "{}{}{}".format(variant_dir, path, suffix)
    return os.path.exists(full_path)


def check_datamaps(args, ds_id):  # noqa: C901
    """
    Check the datamaps for the dataset with ID ds_id
    Return None if the node doesn't exist, otherwise
    return the number of nodes that had errors
    """
    local = args.local
    if args.node_id:
        node_ids = [args.node_id]
    else:
        ds_dir = get_ds_dir(ds_id, local=local)
        try:
            node_ids = os.listdir(ds_dir + "/versions")
        except OSError:
            if args.oneline:
                print("{}@:DELETED".format(ds_id))
                sys.stdout.flush()
            else:
                dprintf(args, "Dataset {} does not exist", ds_id)
            return None
    dprintf(
        args,
        "Checking {} datamaps for dataset {} {}\n",
        len(node_ids),
        ds_id,
        "on local disk" if local else "in the repo",
    )
    result = {}
    for node_id in sorted(node_ids):
        try:
            result[node_id] = check_datamap(args, ds_id, node_id)
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


def check_datamap(args, ds_id, node_id):
    """
    Return the status of this datamap node:
    0 if no columns had errors
    n > 0 if n columns had errors
    < 0 if there was some other major error
    """
    dm = load_datamap(args, ds_id, node_id, local=args.local)
    if not dm:
        # Could not load datamap for this node
        return -101
    return check_datamap_paths(args, ds_id, dm)


def check_datamap_paths(args, ds_id, dm):  # noqa: C901
    """
    dm: Datamap dictionary
    numrows: Number of rows in the frame
    Return the status of this datamap node:
    0 if no columns had errors
    n > 0 if n columns had errors
    < 0 if there was some other major error
    """
    frame = load_frame(args, ds_id, dm)
    numrows = frame["numrows"]
    dprintf(args, "numrows: {}", numrows)
    found_variants = set()
    missing_variants = set()
    missing_paths = {}
    column_errors = 0
    if args.columns:
        variables = load_variables(args, ds_id, dm)
        dprintf(args, "num variables: {}", len(variables))
    else:
        variables = None
    dprintf(args, "num datamap paths: {}", len(dm))
    i = 0
    for path in sorted(dm):
        variant = dm[path]
        if args.progress and i % 100 == 0:
            sys.stdout.write(".")  # One progress dot per hundred paths checked
            sys.stdout.flush()
        i += 1
        if variant not in found_variants:
            if variant not in missing_variants:
                if not variant_dir_exists(ds_id, variant, local=args.local):
                    missing_variants.add(variant)
            if variant in missing_variants:
                missing_paths[path] = variant
                continue
            found_variants.add(variant)
        if args.columns:
            if path.endswith(".data.zz9"):
                if not check_column(args, ds_id, dm, variables, numrows, path):
                    column_errors += 1
            # Paths not ending with .data.zz9:
            # - Related column files - will be checked by check_column()
            # - variables.zz9 - loaded by load_variables() already
            # - frame.zz9 - loaded by load_frame() already
        elif not path_file_exists(ds_id, variant, path, local=args.local):
            missing_paths[path] = variant
    if args.progress:
        sys.stdout.write("\n")
        sys.stdout.flush()
    if not args.oneline:
        if missing_variants:
            print(len(missing_variants), "missing variants:", sorted(missing_variants))
        if missing_paths:
            if args.local:
                print(len(missing_paths), "paths in datamap not downloaded yet")
            else:
                print(len(missing_paths), "paths in datamap not in repo")
        if column_errors:
            print(column_errors, "columns with errors")
        sys.stdout.flush()
    if missing_variants:
        return -102
    if missing_paths and not args.local:
        return -103
    return column_errors


def check_column(args, ds_id, dm, variables, numrows, data_path):  # noqa: C901
    """
    dm: Datamap dict
    variables: Map of var_id to variable definition
    numrows: Number of rows in the frame
    data_path: key in datamap for the .data.zz9 file for a variable

    This duplicates some of the logic in Datamap.load_column() to verify that a
    column can be loaded without actually loading it.

    Return True if it appears the column can be loaded Ok, False otherwise.
    """
    var_id = data_path.rpartition("/")[-1].partition(".")[0]
    vardef = variables.get(var_id)
    classname = None if vardef is None else vardef.get("type", {}).get("class")
    f = open_datafile(args, ds_id, dm, data_path)
    # We already verified this file exists, so this should never fail unless
    # the dataset is being changed while we read it (possible since this script
    # does no locking).
    if f is None:
        eprintf(args, "{}: {} column - Missing .data.zz9 file", data_path, classname)
        return False
    if var_id == "__batch_id__":
        # Ignore these
        return True
    if not vardef:
        eprintf(args, "{}: variable {} not in variables.zz9 file", data_path, var_id)
        return False
    b4 = f.read(4)
    if b4 == b"":
        # Some older formats did this -- I don't want to support those older formats!
        eprintf(args, "{}: {} column - Zero-length data file?", data_path, classname)
        return False
    elif b4 == b"\x93NUM":
        # Numpy header '\0x93NUMPY'
        header = read_numpy_header_after_4(f)
        if header is None:
            eprintf(
                args,
                "{}: numpy {} column data file could not be loaded",
                data_path,
                classname,
            )
            return False
        shape, _, dtype = header
        if shape[0] != numrows:
            eprintf(
                args,
                "{}: numpy {} column length {} does not match existing length {}",
                data_path,
                classname,
                shape[0],
                numrows,
            )
            return False
        if classname in set(["numeric", "datetime"]):
            missing_path = "/primary/{}.missing.zz9".format(var_id)
            if not check_path(args, ds_id, dm, data_path, classname, missing_path):
                return False
            return True
        elif classname == "text":
            if "U" in dtype.str or "S" in dtype.str:
                # Old "structured" format. There should *not*
                # be any "S" but csv_import used to write them.
                missing_path = "/primary/{}.missing.zz9".format(var_id)
                if not check_path(args, ds_id, dm, data_path, classname, missing_path):
                    return False
                return True
            else:
                # New "coded text" format
                buffer_path = "/primary/{}.buffer.zz9".format(var_id)
                if not check_path(args, ds_id, dm, data_path, classname, buffer_path):
                    return False
                return True
        elif classname == "categorical":
            has_internal_ids = dtype.str == "<i2"
            if has_internal_ids:
                # Old format "internal ids".
                pass
            elif dtype.str == "<u2":
                # Newer format, storing uint16 coordinates.
                pass
            else:
                eprintf(
                    args,
                    "{}: numpy {} column has unknown categorical dtype {}",
                    data_path,
                    classname,
                    dtype,
                )
                return False
            return True
        else:
            eprintf(
                args,
                "{}: numpy column has unrecognized type class {}",
                data_path,
                classname,
            )
            return False
    elif b4 == IndexedIO.INDEXED_MAGIC and classname == "categorical":
        return True
    elif b4 == "SPRS" and classname == "categorical":
        eprintf(
            args,
            "{}: {} column: The SPRS format is no longer supported",
            data_path,
            classname,
        )
        return False
    elif b4 == SCALAR_MAGIC:
        # The original code does f.read(8) but it also did f.seek(0) and I can't do that.
        f.read(4)
        d = marshal.loads(f.read())
        if "numrows" in d:
            # Upgrade to format 22/23.
            d["shape"] = (d.pop("numrows"),)
        if d["shape"][0] != numrows:
            eprintf(
                args,
                "{}: scalar {} column length {} does not match existing length {}",
                data_path,
                classname,
                d["shape"][0],
                numrows,
            )
            return False
        return True
    elif b4 == IndexedIO.INDEXED_MAGIC and classname == "text":
        buffer_path = "/primary/{}.buffer.zz9".format(var_id)
        if not check_path(args, ds_id, dm, data_path, classname, buffer_path):
            return False
        return True
    elif b4 == CARDINAL_MAGIC:
        # The original code does f.read(8) but it also did f.seek(0) and I can't do that.
        f.read(4)
        # This gets exception: TypeError: marshal.load() arg must be file
        # d = marshal.load(f)
        # I could do ``marshal.loads(f.read())`` but I'm concerned about memory usage.
        entries_path = "/primary/{}.entries.zz9".format(var_id)
        if not check_path(args, ds_id, dm, data_path, classname, entries_path):
            return False
        return True
    else:
        # I'm not going to support UnstructuredData
        eprintf(
            args,
            "{}: unstructured {} column - don't know how to check it",
            data_path,
            classname,
        )
        return False


def check_path(args, ds_id, dm, data_path, classname, other_path):
    """
    dm: Datamap dict
    data_path: key in datamap for the .data.zz9 file for a variable
    classname: "numeric", "text", etc. depending on variable type
    other_path: key to be checked to see if it exists in the datamap and on disk

    Return True if other_path exists in the datamap and the file exists on disk,
    False otherwise.
    """
    variant = dm.get(other_path)
    if variant is None or (isinstance(variant, six.string_types) and not variant):
        eprintf(
            args,
            "{}: {} column is missing related path {} in datamap",
            data_path,
            classname,
            other_path,
        )
        return False
    if not path_file_exists(ds_id, variant, other_path, local=args.local):
        eprintf(
            args,
            "{}: {} column variant {} missing file for path {}",
            data_path,
            classname,
            variant,
            other_path,
        )
        return False
    return True


def read_numpy_header_after_4(f):
    r"""
    Read a numpy file header, given that the first 4 bytes have already been read.
    Those first 4 bytes must have been b"\x93NUM".
    Return None if the numpy file is not in valid 1.0 format.
    """
    # Read the rest of the magic string
    data = f.read(2)
    if data != b"PY":
        return None

    # Read and check the file format version
    data = f.read(2)
    if len(data) < 2:
        return None
    major, minor = struct.unpack("BB", data)
    if (major, minor) != (1, 0):
        # Not numpy format 1.0
        return None

    # Read the header using numpy's internal header-reading function, which expects
    # the file object to be positioned right after the version number.
    header = np.lib.format.read_array_header_1_0(f)
    return header


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
        "--local", action="store_true", help="Check datamaps on local disk, not in repo"
    )
    parser.add_argument(
        "--oneline", action="store_true", help="Only output line line per dataset"
    )
    parser.add_argument(
        "--columns", action="store_true", help="Check column file consistency"
    )
    parser.add_argument(
        "--progress", action="store_true", help="Show progress dot every 100 columns"
    )
    parser.add_argument(
        "--raise-on-error",
        action="store_true",
        help="Raise DatamapCheckError instead of printing message",
    )
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
