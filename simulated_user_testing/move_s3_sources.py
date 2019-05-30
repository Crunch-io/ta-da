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

import boto
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
    source_bucket_name = config["SOURCE_STORE"]["BUCKET"]
    for source in _get_append_sources_for_dataset(dataset_id):
        s3_url = _get_s3_url(source_bucket_name, source.location)
        if not s3_url:
            continue
        print(s3_url, source.type)


def do_download(args, config):
    dataset_id = args["<dataset-id>"]
    directory_name = args["<directory-name>"]
    sources = _get_append_sources_for_dataset(dataset_id)
    source_config = config["SOURCE_STORE"]
    s3_conn = boto.connect_s3(
        aws_access_key_id=source_config["KEY"],
        aws_secret_access_key=source_config["SECRET"],
    )
    source_bucket = s3_conn.get_bucket(source_config["BUCKET"])
    for source in sources:
        s3_filename = _get_s3_filename(source.location)
        if not s3_filename:
            continue
        dest_filename = s3_filename
        s3_ext = source.type
        if s3_ext:
            if not dest_filename.endswith("." + s3_ext):
                dest_filename += "." + s3_ext
        s3_path = "sourcefiles/{}".format(s3_filename)
        dest_path = os.path.join(directory_name, dest_filename)
        print("Downloading", s3_path, "to", dest_path)
        s3_key = source_bucket.get_key(s3_path, validate=False)
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


def _get_s3_filename(source_location):
    if not source_location.startswith("crunchfile:///"):
        return None
    return source_location[14:]


def _get_s3_url(source_bucket_name, source_location):
    s3_filename = _get_s3_filename(source_location)
    if not s3_filename:
        return None
    return "s3://{}/sourcefiles/{}".format(source_bucket_name, s3_filename)


def _get_append_sources_for_dataset(dataset_id):
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
    return Source.find_all({"id": {"$in": source_ids}})


if __name__ == "__main__":
    sys.exit(main())
