#!/var/lib/crunch.io/venv/bin/python
"""
Read a list of dataset@version pairs and report whether they are in use

In use includes being used as a Source for a append action, or being used as a
fork parent. TODO: Check if a dataset is a target for a dataset view.

Usage:
    check_version_inuse.py [options] <ds-versions-file>

Options:
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]
"""
from __future__ import print_function
import os
import re
import sys

import docopt
from magicbus import bus
from magicbus.plugins import loggers

from cr.lib.entities.actions import Action
from cr.lib.entities.datasets import Dataset
from cr.lib import exceptions
from cr.lib.commands.common import load_settings, startup
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings

DONE_PATTERN = re.compile(
    r"^(?P<timestamp>\S+)\s+(?P<ds_id>\w+)@(?P<node_id>[^:]+):(?P<status>.*)$"
)


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    settings.update(load_settings(settings_yaml))
    startup()


def check_version_inuse(ds_id, node_id):
    try:
        ds = Dataset.find_by_id(id=ds_id, version="master__tip")
    except exceptions.NotFound:
        print("{}@{}:DELETED".format(ds_id, node_id))
        sys.stdout.flush()
        return
    version = "master__tip" if node_id.startswith("__tip") else node_id
    uses = Action.find_dataset_usages(ds_id, dataset_version=version)
    revision = version.partition("__")[2]
    forks = ds.find_forks(revision)
    if not uses and not forks:
        print("{}@{}:UNUSED".format(ds_id, node_id))
    else:
        print(
            "{}@{}:USED:by {} actions, {} fork children".format(
                ds_id, node_id, len(uses), len(forks)
            )
        )
    sys.stdout.flush()


def main():
    args = docopt.docopt(__doc__)
    ds_versions_filename = args["<ds-versions-file>"]
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)

    if ds_versions_filename == "-":
        f = sys.stdin
    else:
        f = open(ds_versions_filename)
    try:
        for line in f:
            line = line.strip()
            m = DONE_PATTERN.match(line)
            if not m:
                raise ValueError("Line not in expected format: {}".format(line))
            ds_id = m.group("ds_id")
            node_id = m.group("node_id")
            check_version_inuse(ds_id, node_id)
    finally:
        if ds_versions_filename != "-":
            f.close()


if __name__ == "__main__":
    sys.exit(main())
