#!/usr/bin/env python3
"""
Create a dataset using the Crunch API

Usage:
    create_dataset.py [options] [<dataset-name>]

Options:
    -i                      Run interactive prompt after dataset creation
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -u USER_NAME            User section in config [default: default]
    -v                      Print verbose messages
    -m METADATA_FILENAME    [default: data/dataset.json]
    -d DATA_FILENAME        [default: data/dataset.csv]

If <dataset-name> is given, it overrides the name in the metadata JSON file.

Pass -d "" (empty data filename) to create an empty dataset.

Example metadata: http://docs.crunch.io/examples/dataset.json
Example data: http://docs.crunch.io/examples/dataset.csv
"""
from __future__ import print_function
import json
import sys

import docopt
import yaml

from crunch_util import (
    connect_pycrunch,
    connection_info_from_config,
    create_dataset,
    create_dataset_from_csv,
)


def main():
    args = docopt.docopt(__doc__)
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)
    metadata_filename = args["-m"]
    data_filename = args["-d"]
    verbose = args["-v"]
    connection_info = connection_info_from_config(config, args)
    site = connect_pycrunch(connection_info, verbose=verbose)
    if data_filename:
        # Assume a "small" dataset, load all metadata into a dict
        with open(metadata_filename, "r") as f:
            metadata = json.load(f)
        with open(data_filename, "rb") as f:
            ds = create_dataset_from_csv(
                site, metadata, f, dataset_name=args["<dataset-name>"], verbose=verbose
            )
    else:
        # Assume a potentially huge amount of metadata
        ds = create_dataset(
            site,
            metadata_filename,
            dataset_name=args["<dataset-name>"],
            verbose=verbose,
        )
    print(ds.self)
    if args["-i"]:
        import IPython

        IPython.embed()


if __name__ == "__main__":
    sys.exit(main())
