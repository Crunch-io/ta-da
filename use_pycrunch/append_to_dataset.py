#!/usr/bin/env python3
"""
Create source and append it to a dataset using the Crunch API

Usage:
    {program} [options] <dataset-id> <filename-or-url>

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -u USER_NAME            User section in config [default: default]
    -v                      Print verbose messages
"""
import sys

import docopt
import yaml

from crunch_util import (
    append_csv_file_to_dataset,
    connect_pycrunch,
    connection_info_from_config,
)


def main():
    args = docopt.docopt(__doc__.format(program=sys.argv[0]))
    verbose = args['-v']
    with open(args['-c']) as f:
        config = yaml.safe_load(f)
    ds_id = args['<dataset-id>']
    filename_or_url = args['<filename-or-url>']
    connection_info = connection_info_from_config(config, args)
    site = connect_pycrunch(connection_info, verbose=verbose)
    ds = site.datasets.by('id')[ds_id].entity
    append_csv_file_to_dataset(site, ds, filename_or_url, verbose=verbose)


if __name__ == '__main__':
    sys.exit(main())
