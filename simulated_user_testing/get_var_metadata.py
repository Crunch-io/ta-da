#!/var/lib/crunch.io/venv/bin/python
"""
Script to list or download the Variables.add_from_metadata action LOBs.
Meant to be run on the backend HTTP server.

Usage:
    get_var_metadata.py [options] list <dataset-id>
    get_var_metadata.py [options] download <dataset-id> <directory-name>

Options:
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]

Suggested directory name pattern: metadata-<short-dataset-name>
"""
from __future__ import print_function
import os
import sys
import traceback

import boto
import boto.s3.key
import docopt
from magicbus import bus
from magicbus.plugins import loggers

import cr.lib.actions
from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    try:
        loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
        log_to_stdout(level=30)
        config = _cr_lib_init(args)
        if args["list"]:
            return do_list(args, config)
        if args["download"]:
            return do_download(args, config)
        raise NotImplementedError("Command not yet implemented.")
    except BaseException:
        # Avoid generating Sentry error
        traceback.print_exc()
        return 1


def do_list(args, config):
    dataset_id = args["<dataset-id>"]
    for action in _get_var_add_from_metadata_actions(dataset_id):
        metadata = action["params"]["variables_metadata"]
        if "LOB" in metadata:
            print(action["key"], action["hash"], "LOB", metadata["LOB"])
            continue
        print(action["key"], action["hash"], "<no LOB>")


def do_download(args, config):
    dataset_id = args["<dataset-id>"]
    directory_name = args["<directory-name>"]
    lob_ids = list(_get_var_add_from_metadata_lobs(dataset_id))
    lob_config = config["ACTION_LOB_STORE"]
    s3_conn = boto.connect_s3(
        aws_access_key_id=lob_config["KEY"], aws_secret_access_key=lob_config["SECRET"]
    )
    lob_bucket = s3_conn.get_bucket(lob_config["BUCKET"])
    for lob_id in lob_ids:
        s3_path = "sourcefiles/{}".format(lob_id)
        dest_path = os.path.join(directory_name, lob_id + "-lob.json")
        print("Downloading", s3_path, "to", dest_path)
        s3_key = lob_bucket.get_key(s3_path, validate=False)
        s3_key.get_contents_to_filename(dest_path)


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    config = load_settings(settings_yaml)
    settings.update(config)
    startup()
    return config


def _get_var_add_from_metadata_actions(dataset_id):
    dataset = Dataset.find_by_id(id=dataset_id, version="master__tip")
    actions = cr.lib.actions.for_dataset(
        dataset,
        None,
        only_successful=True,
        keys=["Variables.add_from_metadata"],
        exclude_keys=None,
        replay_order=True,
    )
    return actions


def _get_var_add_from_metadata_lobs(dataset_id):
    for action in _get_var_add_from_metadata_actions(dataset_id):
        metadata = action["params"]["variables_metadata"]
        if "LOB" not in metadata:
            continue
        yield metadata["LOB"]


if __name__ == "__main__":
    sys.exit(main())
