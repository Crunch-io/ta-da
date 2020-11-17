#!/usr/bin/env python3
"""
Simulate what a Profiles editor would do to set up a dataset

Usage:
    editor_bot.py [options] simulate-editor

Options:
    -c CONFIG_FILE          [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: alpha]
    -u USER_ALIAS           Key to section inside profile [default: sim-editor-1]
    -v                      Log verbose messages
    --dataset-template=TEMPLATE_ID  [default: gb_plus]
    --keep-prev-datasets=N  Number of previous datasets to keep [default: 10]
    --slack-notify          Send Slack message when done
    --stderr                Log to standard error instead of to syslog
    --loglevel=LEVEL        Logging level [default: INFO]
"""
from __future__ import print_function
from contextlib import contextmanager
from datetime import datetime
import glob
import io
import logging
import logging.handlers
import os
import re
import sys
import textwrap
import time

import docopt
from pycrunch.elements import ElementSession
import yaml

import crunch_util
import ds_meta
import ds_data
import sim_util

log = logging.getLogger("editor-bot")


def main():
    args = docopt.docopt(__doc__)
    if args["--stderr"]:
        print("Sending log output to stderr")
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    else:
        print("Sending log output to syslog")
        handler = logging.handlers.SysLogHandler(address="/dev/log")
        handler.setFormatter(
            logging.Formatter(fmt="%(levelname)-8s %(name)s %(message)s")
        )
    sys.stdout.flush()
    level = getattr(logging, args["--loglevel"].upper(), None)
    if level is None:
        raise ValueError("Invalid loglevel: {}".format(args["--loglevel"]))
    logging.getLogger("").setLevel(level)
    logging.getLogger("").addHandler(handler)
    log.info("Starting Editor Bot")
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)
    if args["simulate-editor"]:
        return simulate_editor(config, args)
    raise ValueError("Unknown command")


class ErrorDuringActivity(Exception):
    def __init__(self, activity, err):
        self.activity = activity
        self.err = err

    def __str__(self):
        return "Error while {}: {}".format(self.activity, self.err)

    def __repr__(self):
        return "ErrorDuringActivity({!r}, {!r})".format(self.activity, self.err)


@contextmanager
def track_activity(activity):
    log.info(activity)
    try:
        yield
    except Exception as err:
        log.exception("Error during activity: %s", activity)
        raise ErrorDuringActivity(activity, err)


def simulate_editor(config, args):
    rc = 0
    emoji = ":pizza:"
    saved_user_agent = ElementSession.headers["user-agent"]
    ElementSession.headers["user-agent"] = "editor-bot"
    try:
        msg = _simulate_editor(config, args)
    except ErrorDuringActivity as err:
        rc = 1
        msg = str(err)
        emoji = ":sadpizza:"
    except BaseException as err:
        rc = 2
        msg = "Simulated User Testing: FAILED\n{err}".format(err=err)
        emoji = ":boom:"
        # Need to log traceback here or we won't get one
        log.exception(msg)
    finally:
        ElementSession.headers["user-agent"] = saved_user_agent
        log.info(msg)
        sys.stdout.flush()
        if args["--slack-notify"]:
            response = sim_util.message(
                text=msg,
                channel="#sentry-alpha",
                username="crunchbot",
                icon_emoji=emoji,
            )
            if not response.ok:
                log.error("Problem sending Slack notification: %s", response)
            else:
                log.info("Sent Slack notification")
        else:
            log.info("Not sending Slack notification because --slack-notify not set")
        log.info("Done.")
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
    log.info("Found project Quad; entity_url: %s", quad_project.entity_url)

    # Create the dataset
    msg = 'Creating dataset "{}" from metadata: {}'.format(ds_name, payload_filename)
    with track_activity(msg):
        meta = ds_meta.MetadataModel(verbose=verbose)
    ds = meta.create(site, payload_filename, name=ds_name, project=quad_project)
    log.info("Created dataset: %s", ds.self)

    # Upload the source data and create sources
    source_urls = upload_sources(site, data_dir)

    # Append the data sources (could take up to 1.5 days)
    append_data_sources(site, ds, source_urls, verbose=verbose)

    # Do the infamous Dataset.copy_from
    with track_activity("Getting 'Sim Profiles' project by name"):
        project = sim_util.get_project_by_name(site, "Sim Profiles")
    msg = (
        "Searching for latest good dataset in '{}' project "
        "matching pattern '{}'".format(
            sim_util.get_entity_name(project), ds_name_pattern
        )
    )
    with track_activity(msg):
        prev_ds = sim_util.find_latest_good_dataset_in_project(project, ds_name_pattern)
    if prev_ds is not None:
        msg = "Copying from dataset '{}' to dataset '{}'".format(
            sim_util.get_entity_name(prev_ds), sim_util.get_entity_name(ds)
        )
        with track_activity(msg):
            copy_from(site, prev_ds, ds, verbose=verbose)

    # Create the "Master Fork"
    fork_name_suffix = " - Master Fork"
    msg = "Forking dataset '{}', name suffix: '{}'".format(
        sim_util.get_entity_name(ds), fork_name_suffix
    )
    with track_activity(msg):
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

    # Return message formatted as Slack notification
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
        log.warning("No data files in data dir: %s", data_dir)
        return []
    source_urls = []
    for i, filename in enumerate(chunk_filenames, 1):
        msg = "Uploading chunk {} of {}: {}".format(i, len(chunk_filenames), filename)
        with track_activity(msg):
            source_url = ds_data.upload_source(site, filename)
        source_urls.append(source_url)
        log.info(
            "(%s/%s) Uploaded %s to %s", i, len(chunk_filenames), filename, source_url
        )
    return source_urls


def append_data_sources(site, ds, source_urls, verbose=False):
    timeout = 36000.0  # Batch append can take a long time, giving it 10 hours
    for i, source_url in enumerate(source_urls, 1):
        msg = " ".join(
            [
                "({}/{})".format(i, len(source_urls)),
                "Appending source",
                source_url,
                "to dataset",
                ds.body.id,
            ]
        )
        with track_activity(msg):
            ds_data.append_source(
                site,
                ds,
                source_url,
                i,
                len(source_urls),
                timeout=timeout,
                verbose=verbose,
            )


def copy_from(site, src_ds, dst_ds, verbose=False):
    dst_ds = sim_util.get_entity(dst_ds)
    src_ds_url = sim_util.get_entity_url(src_ds)
    msg = "Running copy_from src={!r}, dst={!r}".format(src_ds_url, dst_ds.self)
    with track_activity(msg):
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
    msg = "Creating fork '{}' in project {}".format(fork_name, project_url)
    with track_activity(msg):
        fork_ds = ds.forks.create({"body": {"name": fork_name, "owner": project_url}})
        fork_ds.refresh()
        return fork_ds


def move_ds_into_project(ds, project):
    project = sim_util.get_entity(project)
    ds_url = sim_util.get_entity_url(ds)
    log.info("Moving dataset %s into project %s", ds_url, project.body.name)
    project.patch({"index": {ds_url: {}}})


def publish_ds(ds):
    ds = sim_util.get_entity(ds)
    log.info("Publishing dataset: %s", ds.self)
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
        log.info(
            "Keeping %s datasets matching pattern %s in project %s (limit is %s)",
            len(datasets),
            repr(ds_name_pattern),
            sim_util.get_entity_name(project),
            keep_prev_datasets,
        )
        return
    num_datasets_to_delete = len(datasets) - keep_prev_datasets
    msg = " ".join(
        [
            "Deleting",
            str(num_datasets_to_delete),
            "old datasets matching pattern",
            repr(ds_name_pattern),
            "in project",
            sim_util.get_entity_name(project),
            "(limit is {})".format(keep_prev_datasets),
        ]
    )
    with track_activity(msg):
        for ds_tuple in datasets[:num_datasets_to_delete]:
            ds = ds_tuple.entity
            log.info("Deleting dataset: %s", ds.body.name)
            # You can't delete a dataset unless you are the current editor
            ds.patch({"current_editor": site.user.self})
            ds.delete()


if __name__ == "__main__":
    sys.exit(main())
