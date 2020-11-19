#!/usr/bin/env python3
"""
Simulate what a Profiles analyst would do when accessing a dataset

Usage:
    user_bot.py [options] cold-load

Options:
    -c CONFIG_FILE          [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: alpha]
    -u USER_ALIAS           Key to section inside profile [default: sim-user-1]
    -v                      Log verbose messages
    --dataset-template=TEMPLATE_ID  [default: gb_plus]
    --stderr                Log to standard error instead of to syslog
    --loglevel=LEVEL        Logging level [default: INFO]

Commands:
    cold-load               Search for an old dataset matching the template and
                            access it. Measure and log the time it takes.
"""
from __future__ import print_function
from collections import defaultdict
import io
import logging
import logging.handlers
import re
import sys
import time

import docopt
from pycrunch.elements import ElementSession
import yaml

import sim_util
from sim_util import ErrorDuringActivity, track_activity

APP_NAME = "user-bot"
log = logging.getLogger(APP_NAME)


def main():
    args = docopt.docopt(__doc__)
    if args["--stderr"]:
        print("Sending {} log output to stderr".format(APP_NAME))
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    else:
        print("Sending {} log output to syslog".format(APP_NAME))
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
    log.info("Starting User Bot")
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)
    saved_user_agent = ElementSession.headers["user-agent"]
    ElementSession.headers["user-agent"] = APP_NAME
    try:
        if args["cold-load"]:
            return simulate_cold_load(config, args)
        raise ValueError("Unknown command")
    except KeyboardInterrupt:
        log.warning("Stopped by KeyboardInterrupt")
        return 1
    except ErrorDuringActivity:
        # Error message has already been logged
        return 2
    except BaseException:
        log.exception("Unexpected exception")
        return 3
    finally:
        ElementSession.headers["user-agent"] = saved_user_agent


def simulate_cold_load(config, args):
    t0 = time.time()
    ds_template_id = args["--dataset-template"]
    ds_name_prefix = sim_util.get_ds_name_prefix(ds_template_id)
    ds_name_pattern = r"^{}".format(re.escape(ds_name_prefix))
    site = sim_util.connect_api(config, args)
    with track_activity(APP_NAME, "Getting 'Sim Profiles' project by name"):
        project = sim_util.get_project_by_name(site, "Sim Profiles")
    msg = "Finding oldest dataset in project '{}' " "matching pattern '{}'".format(
        sim_util.get_entity_name(project), ds_name_pattern
    )
    with track_activity(APP_NAME, msg):
        old_ds = sim_util.find_oldest_good_dataset_in_project(project, ds_name_pattern)
    t1 = time.time()
    with track_activity(APP_NAME, "Do something with oldest dataset"):
        do_something_with_dataset(old_ds)
    tn = time.time()
    log.info("simulate_cold_load         : %.6f seconds", tn - t0)
    log.info("  do_something_with_dataset: %.6f seconds", tn - t1)
    return 1


def do_something_with_dataset(ds):
    """
    ds: Dataset Tuple
    """
    ds_name = sim_util.get_entity_name(ds)
    ds_id = ds.id
    log.info("Found dataset '%s' (%s)", ds_name, ds_id)
    var_count = 0
    derived_count = 0
    hidden_count = 0
    type_count = defaultdict(int)
    for var_tuple in ds.entity.variables.index.values():
        var_count += 1
        derived_count += var_tuple.derived
        hidden_count += var_tuple.hidden
        type_count[var_tuple.type] += 1
    log.info(
        "Dataset '%s' (%s): %d variables: %d derived, %d hidden",
        ds_name,
        ds_id,
        var_count,
        derived_count,
        hidden_count,
    )
    for var_type, n in type_count.items():
        log.info(
            "Dataset '%s' (%s): %d variables of type '%s'", ds_name, ds_id, n, var_type
        )


if __name__ == "__main__":
    sys.exit(main())
