#!/var/lib/crunch.io/venv/bin/python
"""
Iterate over Crunch datasets on Alpha and characterize them by categories

This script requires cr.lib access

Usage:
    characterize_ds_list.py [options] <ds-ids-file>

Options:
    --cr-lib-config=FILENAME    [default: /var/lib/crunch.io/cr.server-0.conf]
    -i                          Run interactive prompt after report
"""
from __future__ import print_function
import code
from datetime import datetime
from math import ceil
import os
import sys

import docopt
from magicbus import bus
from magicbus.plugins import loggers
import numpy as np
import six
from zmq.error import ZMQError

from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib import exceptions
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings
from zz9lib.errors import ZZ9Error

BEGINNING_OF_TIME = datetime(1970, 1, 1)

# These datasets are kept so that the integrity checker has something to report
# and so that migration scripts etc. can get experience dealing with unloadable
# datasets.
BROKEN_DATASETS = [
    "0805b16e79be4e4b98729588b93742c8",  # Missing all frame.zz9.lz4 files
    "120aa3c58ec94ca29bb948d16e737212",  # length 0 does not match existing length
]


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    settings.update(load_settings(settings_yaml))
    startup()


class DatasetStats(object):
    def __init__(self, args):
        self.args = args
        self.broken_ds_ids = set(BROKEN_DATASETS)
        self.ds_info_map = {}  # {ds_id: ds_info}
        self.num_deleted_datasets = 0
        self.problem_datasets = []

    def ingest_dataset(self, ds):
        if ds.id in self.broken_ds_ids:
            return
        ds_info = {}
        # For now assume cached values are correct
        ds_info["num_rows"] = ds.cached.rows
        ds_info["num_cols"] = ds.cached.columns
        ds_info["creation_time"] = (
            ds.creation_time - BEGINNING_OF_TIME
        ).total_seconds()
        self.ds_info_map[ds.id] = ds_info

    def report(self):
        print("Encountered", self.num_deleted_datasets, "deleted datasets")
        print("Encountered", len(self.problem_datasets), "problem datasets")
        print("Successfully ingested", len(self.ds_info_map), "datasets")
        num_rows_data = [d["num_rows"] for d in six.itervalues(self.ds_info_map)]
        num_cols_data = [d["num_cols"] for d in six.itervalues(self.ds_info_map)]
        creation_time_data = [
            d["creation_time"] for d in six.itervalues(self.ds_info_map)
        ]
        min_creation_time = min(creation_time_data)
        median_creation_time = np.median(creation_time_data)
        max_creation_time = max(creation_time_data)
        median_num_rows = int(ceil(np.median(num_rows_data)))
        max_num_rows = max(num_rows_data)
        median_num_cols = int(ceil(np.median(num_cols_data)))
        max_num_cols = max(num_cols_data)
        print("Median number of rows:", median_num_rows)
        print("Maximum number of rows:", max_num_rows)
        print("Median number of columns:", median_num_cols)
        print("Maximum number of columns:", max_num_cols)
        utcfromtimestamp = datetime.utcfromtimestamp
        print("Earliest creation time:", utcfromtimestamp(min_creation_time))
        print("Median creation time:", utcfromtimestamp(median_creation_time))
        print("Latest creation time:", utcfromtimestamp(max_creation_time))
        sys.stdout.flush()

        # Report sample dataset IDs
        for field, median_value, display_func in [
            ("num_rows", median_num_rows, str),
            ("num_cols", median_num_cols, str),
            ("creation_time", median_creation_time, utcfromtimestamp),
        ]:
            print("\n")
            print("Datasets with low, median, and high values for {}".format(field))
            ds_ids = self.find_zero_ds_ids(field)
            if ds_ids:
                print("Zero:")
                print(
                    "{} datasets with zero value for {}. First few IDs: {}".format(
                        len(ds_ids), ds_ids[:3]
                    )
                )
            print("Low:")
            ds_ids = self.find_min_ds_ids(field)
            for ds_id in ds_ids:
                print(
                    "Dataset: {}  {}: {}".format(
                        ds_id, field, display_func(self.ds_info_map[ds_id][field])
                    )
                )
            print("Median:")
            ds_ids = self.find_matching_ds_ids(field, median_value)
            for ds_id in ds_ids:
                print(
                    "Dataset: {}  {}: {}".format(
                        ds_id, field, display_func(self.ds_info_map[ds_id][field])
                    )
                )
            print("High:")
            ds_ids = self.find_max_ds_ids(field)
            for ds_id in ds_ids:
                print(
                    "Dataset: {}  {}: {}".format(
                        ds_id, field, display_func(self.ds_info_map[ds_id][field])
                    )
                )
            sys.stdout.flush()

        # Drop into interactive prompt if "-i" option was given
        if self.args["-i"]:
            namespace = {
                "Dataset": Dataset,
                "np": np,
                "self": self,
                "creation_time_data": creation_time_data,
            }
            code.interact(local=namespace)

    def find_zero_ds_ids(self, field):
        """
        Return IDs of datasets with field value of zero
        """
        ds_info_map = self.ds_info_map
        return sorted(
            ds_id
            for ds_id in ds_info_map
            if field in ds_info_map and not ds_info_map[field]
        )

    def get_sorted_ds_ids(self, field, exclude_zero_values=True, reverse=False):
        """
        Return a list of dataset IDs that have a value for the given field
        The list is sorted by the field value and then by dataset ID
        """
        ds_info_map = self.ds_info_map

        def _keyfunc(ds_id):
            return ds_info_map[ds_id][field]

        result = []
        for ds_id in sorted(ds_info_map):
            ds_info = ds_info_map[ds_id]
            if field not in ds_info:
                continue
            if not ds_info[field] and exclude_zero_values:
                continue
            result.append(ds_id)
        result.sort(key=_keyfunc, reverse=reverse)
        return result

    def find_matching_ds_ids(self, field, value, limit=3, exclude_zero_values=True):
        """
        Return IDs of datasets with field matching or close to the given numeric value
        """
        ds_ids = self.get_sorted_ds_ids(field, exclude_zero_values=exclude_zero_values)
        ds_info_map = self.ds_info_map
        result = []
        prev_ds_id = None
        for ds_id in ds_ids:
            cur_val = ds_info_map[ds_id][field]
            if cur_val < value:
                prev_ds_id = ds_id
                continue
            if cur_val == value:
                result.append(ds_id)
                if len(result) >= limit:
                    break
                prev_ds_id = None
                continue
            # cur_val is greater than value -
            # did we just skip over a median, or did we start out too big?
            if prev_ds_id is not None:
                # We just skipped over a median - return this DS ID and the previous one
                result.extend([prev_ds_id, ds_id])
            break
        return result

    def find_min_ds_ids(self, field, limit=3, exclude_zero_values=True):
        """
        Return IDs of datasets with lowest values for a field
        """
        ds_ids = self.get_sorted_ds_ids(field, exclude_zero_values=exclude_zero_values)
        return ds_ids[:limit]

    def find_max_ds_ids(self, field, limit=3, exclude_zero_values=True):
        """
        Return IDs of datasets with highest values for a field
        """
        ds_ids = self.get_sorted_ds_ids(
            field, exclude_zero_values=exclude_zero_values, reverse=True
        )
        return ds_ids[:limit]


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)
    dataset_stats = DatasetStats(args)
    with open(args["<ds-ids-file>"]) as f:
        try:
            for i, line in enumerate(f):
                if i % 100 == 0:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                ds_id = line
                try:
                    ds = Dataset.find_by_id(id=ds_id, version="master__tip")
                except exceptions.NotFound:
                    dataset_stats.num_deleted_datasets += 1
                    continue
                try:
                    with ds.session():
                        dataset_stats.ingest_dataset(ds)
                except ZMQError:
                    # This happens when Ctrl-C is processed at awkward times
                    raise KeyboardInterrupt()
                except ZZ9Error:
                    dataset_stats.problem_datasets.append(ds_id)
        except KeyboardInterrupt:
            print("\nStopped by KeyboardInterrupt")
    print()
    sys.stdout.flush()
    dataset_stats.report()


if __name__ == "__main__":
    sys.exit(main())
