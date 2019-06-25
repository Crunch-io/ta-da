#!/usr/bin/env python3
"""
Simulate what a Profiles editor would do to set up a dataset

Usage:
    editor_bot.py [options] simulate-editor

Options:
    -c CONFIG_FILE          [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: alpha]
    -u USER_ALIAS           Key to section inside profile [default: sim-editor-1]
    -v                      Print verbose messages
    --dataset-template=TEMPLATE_ID  [default: gb_plus]
"""
from __future__ import print_function
from datetime import datetime
import glob
import io
import os
import sys

import docopt
import yaml

import ds_meta
import ds_data
from sim_util import connect_api, get_project_by_name


def main():
    args = docopt.docopt(__doc__)
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)
    if args["simulate-editor"]:
        return simulate_editor(config, args)
    raise ValueError("Unknown command")


def simulate_editor(config, args):
    verbose = args["-v"]
    ds_template_id = args["--dataset-template"]
    ds_template = config["dataset_templates"][ds_template_id]
    payload_filename = ds_template["create_payload"]
    ds_name = generate_ds_name(ds_template_id)
    data_dir = ds_template["data_dir"]
    site = connect_api(config, args)

    project_quad = get_project_by_name(site, "Quad")
    print("Found project Quad; entity_url:", project_quad.entity_url)

    # Create the dataset
    print('Creating dataset "{}" from metadata: {}'.format(ds_name, payload_filename))
    meta = ds_meta.MetadataModel(verbose=verbose)
    ds = meta.create(site, payload_filename, name=ds_name, project=project_quad)
    print("Created dataset:", ds.self)

    # Upload the source data and create sources
    source_urls = upload_sources(site, data_dir)

    # Append the data sources (could take up to 1.5 days)
    append_data_sources(site, ds, source_urls, verbose=verbose)

    print("Done.")
    # TODO: Send Slack notification


def generate_ds_name(ds_template_id):
    t = datetime.now()
    return "Sim {} {}".format(ds_template_id, t.strftime("%Y-%m-%d %H:%M:%S"))


def upload_sources(site, data_dir):
    """
    Return list of created source URLs
    """
    chunk_filenames = glob.glob(os.path.join(data_dir, "*"))
    if not chunk_filenames:
        print("No data files in", data_dir)
        return []
    source_urls = []
    for i, filename in enumerate(chunk_filenames, 1):
        source_url = ds_data.upload_source(site, filename)
        source_urls.append(source_url)
        print(
            "({}/{})".format(i, len(chunk_filenames)),
            "Uploaded",
            filename,
            "to",
            source_url,
        )
        sys.stdout.flush()
    return source_urls


def append_data_sources(site, ds, source_urls, verbose=False):
    for i, source_url in enumerate(source_urls, 1):
        print(
            "({}/{})".format(i, len(source_urls)),
            "Appending source",
            source_url,
            "to dataset",
            ds.body.id,
        )
        sys.stdout.flush()  # Make sure progress shows up on stdout
        ds_data.append_source(site, ds, source_url, verbose=verbose)


if __name__ == "__main__":
    sys.exit(main())
