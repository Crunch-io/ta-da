#!/var/lib/crunch.io/venv/bin/python
# Created by David H 2020-08-29
"""
Check text variables to see if they were messed up by convert_to_coded_text

Usage:
    check_text_vars.py [options] <ds-id>
    check_text_vars.py [options] --ids-file=FILENAME

Options:
    --cr-lib-config=FILENAME    [default: /var/lib/crunch.io/cr.server-0.conf]
    -i                          Interactive Python prompt
    --oneline                   One line per dataset report
    --chunksize=N               Read column values N at a time, 0 means whole column
                                [default: 0]
"""
from __future__ import print_function
import collections
import os
import sys
import time
import traceback

import docopt
from magicbus import bus
from magicbus.plugins import loggers
from six.moves import xrange

from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets import Dataset
from cr.lib.exceptions import NotFound
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings
from zz9lib.errors import ZZ9ClientTimeout

ACTION_KEYS = (
    "Dataset.execute",
    "Dataset.set_exclusion",
    "Variable.create",
    "Variable.edit_derivation",
)


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    settings.update(load_settings(settings_yaml))
    startup()


def _do_the_thing(args):
    if args["--ids-file"]:
        ds_ids = []
        with open(args["--ids-file"]) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                ds_ids.append(line)
    else:
        ds_ids = [args["<ds-id>"]]
    print("Processing {} datasets".format(len(ds_ids)))
    sys.stdout.flush()
    for ds_id in ds_ids:
        try:
            ds = Dataset.find_by_id(id=ds_id, version="master__tip")
        except NotFound:
            print("{}: DELETED".format(ds_id))
            sys.stdout.flush()
            continue
        try:
            with ds.session():
                _check_text_vars_on_dataset(args, ds)
        except Exception as err:
            if not args["--oneline"]:
                raise
            print("{}: ERROR {}".format(ds_id, err))
            sys.stdout.flush()
        except KeyboardInterrupt:
            print("\nBreak")
        else:
            if args["--oneline"]:
                print("{}: OK".format(ds_id))
                sys.stdout.flush()
            else:
                print()


def _check_text_vars_on_dataset(args, ds):  # noqa: C901
    """Raise RuntimeError or other exception if error found loading text vars"""
    if not args["--oneline"]:
        print("Checking text variables in dataset {}".format(ds.id))
        sys.stdout.flush()
    numrows = dataset_numrows(ds)
    r = ds.primary.describe()
    num_vars = len(r)
    text_var_aliases = [
        i[1]["references"]["alias"] for i in r if i[1]["type"]["class"] == "text"
    ]

    # The find_many_by_ids() method sometimes crashes.
    # text_var_ids = [i[0] for i in r if i[1]["type"]["class"] == "text"]
    # r = ds.variables.find_many_by_ids(text_var_ids, output="admin_describe")["result"]
    r = ds.primary.query({"command": "admin_describe"})["result"]
    text_var_structs = [i["structure"] for i in r if i["type"]["class"] == "text"]
    struct_val_counts = collections.defaultdict(int)
    for text_var_struct in text_var_structs:
        struct_val_counts[text_var_struct] += 1
    non_migrated = set(struct_val_counts) - {"coded text", "indexed text"}

    if not args["--oneline"]:
        print(
            "{}/{} variables are text variables".format(len(text_var_aliases), num_vars)
        )
        for text_var_struct in sorted(struct_val_counts):
            print(
                "Structure: {!r}  Num. variables: {}".format(
                    text_var_struct, struct_val_counts[text_var_struct]
                )
            )
        print(
            "Number of non-migrated text variables: {}".format(
                sum(struct_val_counts[k] for k in non_migrated)
            )
        )
        print("numrows: {}".format(numrows))
        sys.stdout.flush()

    num_unique_vals_counts = collections.defaultdict(int)
    errors = []
    max_errors = 3

    def _add_error(errmsg):
        errors.append(errmsg)
        if len(errors) >= max_errors:
            raise RuntimeError("; ".join(errors))

    def _check_errors():
        if errors:
            raise RuntimeError("; ".join(errors))

    for var_alias in text_var_aliases:
        try:
            data = _load_column_values(args, numrows, ds, var_alias)
        except Exception as err:
            _add_error("{}: {}: {}".format(var_alias, err.__class__.__name__, err))
            continue

        if len(data) != numrows:
            _add_error(
                "{}: Found {} rows when previous numrows={}".format(
                    var_alias, len(data), numrows
                )
            )

        def _turn_missing_dict_to_tuple(d):
            if not isinstance(d, dict):
                return d
            if "?" not in d or len(d) != 1:
                _add_error(
                    "{}: Text value in unexpected format: {}".format(var_alias, d)
                )
            return ("?", d["?"])

        data = [_turn_missing_dict_to_tuple(i) for i in data]
        n = len(set(data))
        num_unique_vals_counts[n] += 1

    _check_errors()

    if not args["--oneline"]:
        print(
            "[(count_of_unique_text_vals, number_of_variables_with_that_count),...] :"
        )
        print([(n, num_unique_vals_counts[n]) for n in sorted(num_unique_vals_counts)])
        sys.stdout.flush()


def dataset_numrows(ds):
    """
    Return the number of rows in the dataset, ignoring any weight or filter.

    See also: FrameSummaryMixin.count() and CrunchFrame.select_cube()
    """
    return ds.primary.cube({"count": {"function": "cube_count", "args": []}})[
        "measures"
    ]["count"]["data"][0]


def _load_column_values(args, numrows, ds, var_alias):
    chunksize = int(args["--chunksize"])
    v = ds.variables.get(alias=var_alias)
    if chunksize > 0:
        data = []
        for i in xrange(0, numrows, chunksize):
            r = ds.primary.select(
                {var_alias: v.reference},
                filter=None,
                offset=i,
                limit=min(chunksize, numrows - i),
            )
            response_data = r["data"]
            if not isinstance(response_data, dict):
                raise RuntimeError("select response is not a dict")
            if var_alias not in response_data:
                raise RuntimeError(
                    "select response does not include key {!r}".format(var_alias)
                )
            data.extend(response_data[var_alias])
        return data
    else:
        for i in range(2):
            try:
                return ds.primary.read(v.reference)["data"]
            except ZZ9ClientTimeout:
                if i == 0:
                    # Retry on first timeout
                    continue
                raise


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)
    t0 = time.time()
    try:
        _do_the_thing(args)
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        t1 = time.time()
        print(t1 - t0, "seconds")


if __name__ == "__main__":
    sys.exit(main())
