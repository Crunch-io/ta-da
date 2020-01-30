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
    --slack-notify          Send Slack message when done
"""
from __future__ import print_function
from datetime import datetime
import glob
import io
import os
import re
import sys
import textwrap
import time
import traceback

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
    try:
        rc = 0
        msg = _simulate_editor(config, args)
    except BaseException as err:
        rc = 1
        msg = "Simulated User Testing: FAILED\n{err}".format(err=err)
        traceback.print_exc()
    finally:
        print(msg)
        if args["--slack-notify"]:
            response = sim_util.message(
                text=msg,
                channel="#sentry-alpha",
                username="crunchbot",
                icon_emoji=":pizza:",
            )
            if not response.ok:
                print("ERROR sending Slack notification:", response)
            else:
                print("Sent Slack notification")
        else:
            print("Not sending Slack notification because --slack-notify not set")
        print("Done.")
        return rc


def _simulate_editor(config, args):
    """
    Do what an Editor does to set up a new Profiles dataset
    Return a string status message formatted for Slack
    """
    t0 = time.time()
    verbose = args["-v"]
    ds_template_id = args["--dataset-template"]
    keep_prev_datasets = int(args["--keep-prev-datasets"])
    ds_template = config["dataset_templates"][ds_template_id]
    payload_filename = ds_template["create_payload"]
    ds_name_prefix = get_ds_name_prefix(ds_template_id)
    ds_name_pattern = r"^{}".format(re.escape(ds_name_prefix))
    ds_name = generate_ds_name(ds_name_prefix)
    data_dir = ds_template["data_dir"]
    environment = args["-p"]  # profile name == environment (e.g. alpha)
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
    prev_ds = sim_util.find_latest_good_dataset_in_project(project, ds_name_pattern)
    if prev_ds is not None:
        copy_from(site, prev_ds, ds, verbose=verbose)

    # Create the "Master Fork"
    fork_name_suffix = " - Master Fork"
    fork_ds = create_fork(site, ds, quad_project, fork_name_suffix)

    # Delete older dataset forks in this series
    forked_ds_name_pattern = r"^{}.*{}$".format(
        re.escape(ds_name_prefix), re.escape(fork_name_suffix)
    )
    trim_older_datasets(site, quad_project, forked_ds_name_pattern, keep_prev_datasets)

    # Move into the project where it will be published
    move_ds_into_project(ds, project)

    # Publish the dataset
    publish_ds(ds)

    # Move the previous dataset into the Previous sub-project
    prev_project = sim_util.get_subproject_by_name(project, "Previous")
    prev_project = sim_util.get_entity(prev_project)
    if prev_ds is not None:
        move_ds_into_project(prev_ds, prev_project)

    # Delete older datasets in Previous project
    trim_older_datasets(site, prev_project, ds_name_pattern, keep_prev_datasets)

    # Send Slack notification
    msg = (
        textwrap.dedent(
            """
        *Simulated User Testing*
        _editor_bot_ ran in {environment} environment in {duration:.1f} seconds
        Created dataset "{ds_name}"
        Appended {num_batches} batches
        Ran Dataset.copy_from({prev_ds_name})
        Created fork: "{fork_ds_name}"
        Published to "{project_name}"
        """
        )
        .strip()
        .format(
            environment=environment,
            duration=(time.time() - t0),
            ds_name=ds.body.name,
            num_batches=len(source_urls),
            prev_ds_name=("" if prev_ds is None else sim_util.get_entity_name(prev_ds)),
            fork_ds_name=sim_util.get_entity_name(fork_ds),
            project_name=sim_util.get_entity_name(project),
        )
    )
    return msg


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
        timeout = 36000.0  # Batch append can take a long time, giving it 10 hours
        ds_data.append_source(
            site, ds, source_url, i, len(source_urls), timeout=timeout, verbose=verbose
        )


def copy_from(site, src_ds, dst_ds, verbose=False):
    dst_ds = sim_util.get_entity(dst_ds)
    src_ds_url = sim_util.get_entity_url(src_ds)
    print("Running copy_from src={!r}, dst={!r}".format(src_ds_url, dst_ds.self))
    t0 = datetime.utcnow()
    response = dst_ds.patch(
        {"element": "shoji:entity", "body": {"copy_from": src_ds_url}}
    )
    timeout = 36000.0  # copy_from can take a long time, giving it 10 hours
    try:
        crunch_util.wait_for_progress2(site, response, timeout, verbose=verbose)
    except Exception as err:
        msg = (
            "Error running copy_from command: {err}\n"
            "Source dataset URL: {src_ds_url}\n"
            "Destination dataset URL: {dst_ds.self}\n"
            "Request originally sent at {t0} UTC"
        ).format(err=err, src_ds_url=src_ds_url, dst_ds=dst_ds, t0=t0)
        raise Exception(msg)


def create_fork(site, ds, project, fork_name_suffix):
    fork_name = "{}{}".format(ds.body.name, fork_name_suffix)
    project_url = sim_util.get_entity_url(project)
    print("Creating", fork_name, "in project", project_url)
    fork_ds = ds.forks.create({"body": {"name": fork_name, "owner": project_url}})
    fork_ds.refresh()
    return fork_ds


def move_ds_into_project(ds, project):
    project = sim_util.get_entity(project)
    ds_url = sim_util.get_entity_url(ds)
    print("Moving dataset", ds_url, "into project", project.body.name)
    project.patch({"index": {ds_url: {}}})


def publish_ds(ds):
    ds = sim_util.get_entity(ds)
    print("Publishing dataset", ds.self)
    ds.patch({"is_published": True})


def trim_older_datasets(site, project, ds_name_pattern, keep_prev_datasets):
    """
    keep_prev_datasets: Number of datasets to keep in project metching name regex
    """
    if keep_prev_datasets < 1:
        raise ValueError("keep_prev_datasets must be >= 1")
    datasets = sim_util.sort_ds_tuples_by_creation_datetime(
        sim_util.yield_project_datasets_matching_name(project, ds_name_pattern),
        reverse=False,
    )
    if len(datasets) <= keep_prev_datasets:
        print(
            "Keeping",
            len(datasets),
            "datasets matching pattern",
            repr(ds_name_pattern),
            "in project",
            sim_util.get_entity_name(project),
            "(limit is {})".format(keep_prev_datasets),
        )
        return
    num_datasets_to_delete = len(datasets) - keep_prev_datasets
    print(
        "Deleting",
        num_datasets_to_delete,
        "old datasets matching pattern",
        repr(ds_name_pattern),
        "in project",
        sim_util.get_entity_name(project),
        "(limit is {})".format(keep_prev_datasets),
    )
    for ds_tuple in datasets[:num_datasets_to_delete]:
        ds = ds_tuple.entity
        print("Deleting", ds.body.name)
        # You can't delete a dataset unless you are the current editor
        ds.patch({"current_editor": site.user.self})
        ds.delete()


if __name__ == "__main__":
    sys.exit(main())
