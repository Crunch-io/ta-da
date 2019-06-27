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
    --keep-prev-datasets=N  Number of previous datasets to keep [default: 10]
"""
from __future__ import print_function
from datetime import datetime
import glob
import io
import os
import sys

import docopt
import yaml

import crunch_util
import ds_meta
import ds_data
import sim_util


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
    keep_prev_datasets = int(args["--keep-prev-datasets"])
    ds_template = config["dataset_templates"][ds_template_id]
    payload_filename = ds_template["create_payload"]
    ds_name_prefix = get_ds_name_prefix(ds_template_id)
    ds_name = generate_ds_name(ds_name_prefix)
    data_dir = ds_template["data_dir"]
    site = sim_util.connect_api(config, args)

    quad_project = sim_util.get_project_by_name(site, "Quad")
    print("Found project Quad; entity_url:", quad_project.entity_url)

    # Create the dataset
    print('Creating dataset "{}" from metadata: {}'.format(ds_name, payload_filename))
    meta = ds_meta.MetadataModel(verbose=verbose)
    ds = meta.create(site, payload_filename, name=ds_name, project=quad_project)
    print("Created dataset:", ds.self)

    # Upload the source data and create sources
    source_urls = upload_sources(site, data_dir)

    # Append the data sources (could take up to 1.5 days)
    append_data_sources(site, ds, source_urls, verbose=verbose)

    # Do the infamous Dataset.copy_from
    project = sim_util.get_project_by_name(site, "Sim Profiles")
    copy_from_last_successful_ds(site, project, ds_name_prefix, ds, verbose=verbose)

    # Create the "Master Fork"
    create_master_fork(site, ds)

    # Move into the project where it will be published
    # But first save a reference to the previous latest good dataset there
    prev_ds = sim_util.find_latest_good_dataset_in_project(project, ds_name_prefix)
    assert prev_ds.entity_url != ds.self
    move_ds_into_project(ds, project)

    # Publish the dataset
    publish_ds(ds)

    # Move the previous dataset into the Previous sub-project
    prev_project = sim_util.get_subproject_by_name(project, "Previous")
    prev_project = sim_util.get_entity(prev_project)
    if prev_ds is not None:
        move_ds_into_project(prev_ds, prev_project)

    # Delete older datasets in Previous project
    trim_older_datasets(prev_project, ds_name_prefix, keep_prev_datasets)

    print("Done.")
    # TODO: Send Slack notification


def get_ds_name_prefix(template_id):
    return "Sim {}".format(template_id)


def generate_ds_name(ds_name_prefix):
    t = datetime.now()
    return "{} {}".format(ds_name_prefix, t.strftime("%Y-%m-%d %H:%M:%S"))


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


def copy_from_last_successful_ds(site, project, ds_name_prefix, ds, verbose=False):
    prev_ds_tuple = sim_util.find_latest_good_dataset_in_project(
        project, ds_name_prefix
    )
    if prev_ds_tuple is None:
        print("No previous dataset found, no copy_from will be performed.")
        return
    print(
        "Running copy_from src={!r}, dst={!r}".format(ds.self, prev_ds_tuple.entity_url)
    )
    response = ds.patch(
        {"element": "shoji:entity", "body": {"copy_from": prev_ds_tuple.entity_url}}
    )
    timeout = 3600.0 * 6  # copy_from can take a long time
    crunch_util.wait_for_progress2(site, response, timeout, verbose=verbose)


def create_master_fork(site, ds):
    fork_name = "{} - Master Fork".format(ds.body.name)
    print("Creating", fork_name)
    ds.forks.create({"body": {"name": fork_name}})


def move_ds_into_project(ds, project):
    project = sim_util.get_entity(project)
    ds_url = sim_util.get_entity_url(ds)
    print("Moving dataset", ds_url, "into project", project.body.name)
    project.patch({"index": {ds_url: {}}})


def publish_ds(ds):
    ds = sim_util.get_entity(ds)
    print("Publishing dataset", ds.self)
    ds.patch({"is_published": True})


def trim_older_datasets(project, prefix, keep_prev_datasets):
    """
    keep_prev_datasets: Number of datasets to keep in project metching name prefix
    """
    assert keep_prev_datasets >= 1
    datasets = [
        ds_tuple
        for _, ds_tuple in sim_util.sort_project_datasets_by_creation_datetime(
            project, reverse=False
        )
        if ds_tuple.name.startswith(prefix)
    ]
    if len(datasets) > keep_prev_datasets:
        num_datasets_to_delete = len(datasets) - keep_prev_datasets
        print(
            "Deleting",
            num_datasets_to_delete,
            "old datasets in project",
            project.body.name,
        )
        for ds_tuple in datasets[:num_datasets_to_delete]:
            ds = ds_tuple.entity
            print("Deleting", ds.body.name)
            ds.delete()


if __name__ == "__main__":
    sys.exit(main())
