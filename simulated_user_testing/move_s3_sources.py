#!/var/lib/crunch.io/venv/bin/python
"""
Script to list/download/upload S3 sources for a dataset

Usage:
    move_s3_sources.py [options] list <dataset-id>
    move_s3_sources.py [options] download <dataset-id> <directory-name>
    move_s3_sources.py [options] upload <directory-name>

Options:
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]
"""
from __future__ import print_function
import os
import sys
import traceback

import docopt
from magicbus import bus
from magicbus.plugins import loggers

import cr.lib.actions
from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib.entities.sources import Source
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    try:
        loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
        log_to_stdout(level=30)
        _cr_lib_init(args)
        if args["list"]:
            return do_list(args)
        raise NotImplementedError("Command not yet implemented.")
    except BaseException:
        # Avoid generating Sentry error
        traceback.print_exc()
        return 1


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    config = load_settings(settings_yaml)
    settings.update(config)
    startup()
    return config


def do_list(args):
    dataset_id = args["<dataset-id>"]
    dataset = Dataset.find_by_id(id=dataset_id, version="master__tip")
    actions = cr.lib.actions.for_dataset(
        dataset,
        None,
        only_successful=True,
        keys=["Source.append"],
        exclude_keys=None,
        replay_order=True,
    )
    source_ids = [action["params"]["source"] for action in actions]
    for source in Source.find_all({"id": {"$in": source_ids}}):
        print(source.location, source.type)


if __name__ == "__main__":
    sys.exit(main())
